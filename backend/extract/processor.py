import os
import struct
import tempfile

import requests
from django.conf import settings

from . import b2
from .models import Video

SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"
CHUNK_SECONDS = 28


def _format_ts(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _transcribe(api_key, audio_path, offset=0):
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {
            "model": "saaras:v3",
            "mode": "transcribe",
            "with_timestamps": "true",
            "language_code": "unknown",
        }
        resp = requests.post(
            SARVAM_API_URL, headers={"api-subscription-key": api_key},
            files=files, data=data,
        )
    result = resp.json()
    segments = []
    ts = result.get("timestamps")
    if ts and ts.get("words"):
        for i in range(len(ts["words"])):
            segments.append({
                "text": ts["words"][i],
                "start": ts["start_time_seconds"][i] + offset,
                "end": ts["end_time_seconds"][i] + offset,
            })
    else:
        text = result.get("transcript", "")
        if text:
            segments.append({"text": text, "start": offset, "end": offset + 1})
    return segments


def _split_segments(segments, max_words=8):
    result = []
    for seg in segments:
        words = seg["text"].split()
        if len(words) <= max_words:
            result.append(seg)
            continue
        duration = seg["end"] - seg["start"]
        num_chunks = (len(words) + max_words - 1) // max_words
        chunk_dur = duration / num_chunks
        for i in range(num_chunks):
            chunk_words = words[i * max_words : (i + 1) * max_words]
            chunk_start = seg["start"] + i * chunk_dur
            chunk_end = chunk_start + chunk_dur - 0.05 if i < num_chunks - 1 else seg["end"]
            if chunk_end <= chunk_start:
                chunk_end = chunk_start + 0.5
            result.append({
                "text": " ".join(chunk_words),
                "start": chunk_start,
                "end": chunk_end,
            })
    return result


def _build_srt(segments):
    lines = []
    for i, s in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_format_ts(s['start'])} --> {_format_ts(s['end'])}")
        lines.append(s["text"])
        lines.append("")
    return "\n".join(lines)


def _wav_info(path):
    """Return (num_channels, sample_rate, bits_per_sample, data_bytes, data_offset)."""
    with open(path, "rb") as f:
        riff = f.read(12)
        if riff[:4] != b"RIFF" or riff[8:12] != b"WAVE":
            raise ValueError("not a WAV file")
        num_channels = 1
        sample_rate = 0
        bits_per_sample = 16
        data_bytes = 0
        data_offset = None
        while True:
            start = f.tell()
            chunk = f.read(8)
            if len(chunk) < 8:
                break
            chunk_id, chunk_size = chunk[:4], struct.unpack("<I", chunk[4:8])[0]
            if chunk_id == b"fmt ":
                fmt = f.read(chunk_size)
                num_channels = struct.unpack("<H", fmt[2:4])[0]
                sample_rate = struct.unpack("<I", fmt[4:8])[0]
                bits_per_sample = struct.unpack("<H", fmt[14:16])[0]
            elif chunk_id == b"data":
                data_offset = start + 8
                data_bytes = chunk_size
                break
            else:
                f.seek(start + 8 + chunk_size + (chunk_size % 2))
    if not sample_rate or data_bytes <= 0 or data_offset is None:
        raise ValueError("invalid WAV")
    return num_channels, sample_rate, bits_per_sample, data_bytes, data_offset


def _wav_duration(path):
    num_channels, sample_rate, bits_per_sample, data_bytes, _ = _wav_info(path)
    bytes_per_sample = (bits_per_sample // 8) * num_channels
    return data_bytes / (sample_rate * bytes_per_sample)


def _wav_header(num_channels, sample_rate, bits_per_sample, data_size):
    block_align = (bits_per_sample // 8) * num_channels
    byte_rate = sample_rate * block_align
    fmt = struct.pack("<HHIIHH", 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
    return (
        b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
        + b"fmt " + struct.pack("<I", 16) + fmt
        + b"data" + struct.pack("<I", data_size)
    )


def _split_wav(path, out_dir, chunk_seconds=CHUNK_SECONDS):
    """Split a WAV file into chunk_seconds-long WAV chunks (pure Python, no ffmpeg)."""
    num_channels, sample_rate, bits_per_sample, data_bytes, data_offset = _wav_info(path)
    bytes_per_second = sample_rate * ((bits_per_sample // 8) * num_channels)
    chunk_bytes = max(1, int(chunk_seconds * bytes_per_second))
    chunks = []
    with open(path, "rb") as f:
        f.seek(data_offset)
        remaining = data_bytes
        index = 0
        while remaining > 0:
            size = min(chunk_bytes, remaining)
            data = f.read(size)
            chunk_path = os.path.join(out_dir, f"chunk_{index:03d}.wav")
            with open(chunk_path, "wb") as cf:
                cf.write(_wav_header(num_channels, sample_rate, bits_per_sample, len(data)))
                cf.write(data)
            chunks.append(chunk_path)
            remaining -= size
            index += 1
    return chunks


def process_video(vid_id):
    video = Video.objects.get(id=vid_id)

    api_key = os.environ.get("SARVAM_API_KEY", "")
    if not api_key:
        video.status = "failed"
        video.save()
        raise RuntimeError("SARVAM_API_KEY not set")

    if not video.audio_file:
        video.status = "failed"
        video.save()
        raise RuntimeError("audio_file is required")

    audio_path = video.audio_file.path
    base = os.path.splitext(os.path.basename(audio_path))[0]

    dur = _wav_duration(audio_path)

    all_segments = []
    if dur <= CHUNK_SECONDS:
        all_segments = _transcribe(api_key, audio_path)
    else:
        chunk_dir = tempfile.mkdtemp()
        chunks = _split_wav(audio_path, chunk_dir, CHUNK_SECONDS)
        offset = 0.0
        for cf in chunks:
            cd = _wav_duration(cf)
            all_segments.extend(_transcribe(api_key, cf, offset))
            offset += cd

    max_words = (video.caption_style or {}).get("maxWords", 8)
    all_segments = _split_segments(all_segments, max_words)

    srt_content = _build_srt(all_segments)
    srt_path = os.path.join(os.path.dirname(audio_path), f"{base}.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    video.subtitle_file = os.path.relpath(srt_path, settings.MEDIA_ROOT)
    video.transcript = all_segments
    video.srt_content = srt_content

    b2_prefix = f"{base}_{vid_id}"
    try:
        video.audio_url = b2.upload(audio_path, f"{b2_prefix}_audio.wav")
        video.subtitle_url = b2.upload(srt_path, f"{b2_prefix}_captions.srt")
    except Exception:
        pass

    video.status = "done"
    video.save()
