import os
import struct
import subprocess
import tempfile

import requests

from . import b2
from .models import Video

SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"


def _format_ts(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _hex_to_ass(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}"
    return "&H00FFFFFF"


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


def _write_srt(segments, path):
    lines = []
    for i, s in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_format_ts(s['start'])} --> {_format_ts(s['end'])}")
        lines.append(s["text"])
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _wav_duration(path):
    """Read duration (seconds) from a WAV file's RIFF header."""
    with open(path, "rb") as f:
        header = f.read(12)
        if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
            raise ValueError("not a WAV file")
        num_channels = 1
        sample_rate = 0
        bits_per_sample = 16
        data_bytes = 0
        while True:
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
                data_bytes = chunk_size
                break
            else:
                f.seek(chunk_size + (chunk_size % 2), 1)
    if not sample_rate or not data_bytes:
        raise ValueError("invalid WAV")
    bytes_per_sample = (bits_per_sample // 8) * num_channels
    return data_bytes / (sample_rate * bytes_per_sample)


def _get_duration(path):
    try:
        return _wav_duration(path)
    except Exception:
        return float(
            subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", path],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
        )


def process_video(vid_id):
    video = Video.objects.get(id=vid_id)

    api_key = os.environ.get("SARVAM_API_KEY", "")
    if not api_key:
        video.status = "failed"
        video.save()
        raise RuntimeError("SARVAM_API_KEY not set")

    video_path = video.video_file.path
    video_dir = os.path.dirname(video_path)
    media_root = os.path.dirname(video_dir)
    base = os.path.splitext(os.path.basename(video_path))[0]

    if video.audio_file:
        audio_path = video.audio_file.path
    else:
        audio_path = os.path.join(video_dir, f"{base}_audio.wav")
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", audio_path, "-y"],
            check=True, capture_output=True,
        )
        video.audio_file = os.path.relpath(audio_path, media_root)
        video.save()

    dur = _get_duration(audio_path)

    all_segments = []
    if dur <= 28:
        all_segments = _transcribe(api_key, audio_path)
    else:
        import glob
        chunk_dir = tempfile.mkdtemp()
        subprocess.run(
            ["ffmpeg", "-i", audio_path, "-f", "segment",
             "-segment_time", "28", os.path.join(chunk_dir, "chunk_%03d.wav"), "-y"],
            check=True, capture_output=True,
        )
        offset = 0.0
        for cf in sorted(glob.glob(os.path.join(chunk_dir, "chunk_*.wav"))):
            cd = float(
                subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", cf],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()
            )
            all_segments.extend(_transcribe(api_key, cf, offset))
            offset += cd

    max_words = (video.caption_style or {}).get("maxWords", 8)
    all_segments = _split_segments(all_segments, max_words)

    srt_path = os.path.join(video_dir, f"{base}.srt")
    _write_srt(all_segments, srt_path)

    style = video.caption_style or {}
    font = style.get("font", "Arial")
    font_size = style.get("fontSize", 26)
    color = _hex_to_ass(style.get("fontColor", "#FFFFFF"))
    bg = _hex_to_ass(style.get("bgColor", "#000000"))
    bg_op = style.get("bgOpacity", 0.7)
    pos = style.get("position", "bottom")
    mv = {"bottom": 50, "top": 650, "center": 360}.get(pos, 50)

    captioned_path = os.path.join(video_dir, f"{base}_captioned.mp4")
    subprocess.run(
        ["ffmpeg", "-i", video_path,
         "-vf",
         f"subtitles={srt_path}:force_style="
         f"'FontName={font},FontSize={font_size},"
         f"PrimaryColour={color},OutlineColour={bg},"
         f"BackColour=&H{int(bg_op*255):02X}000000,"
         f"BorderStyle=1,Outline=2,Shadow=1,"
         f"Alignment=2,MarginV={mv}'",
         "-c:a", "aac", "-b:a", "192k",
         "-preset", "fast", captioned_path, "-y"],
        check=True, capture_output=True,
    )

    video.subtitle_file = os.path.relpath(srt_path, media_root)
    video.captioned_video = os.path.relpath(captioned_path, media_root)
    video.transcript = all_segments

    b2_prefix = f"{base}_{vid_id}"

    try:
        video.video_url = b2.upload(video_path, f"{b2_prefix}_original.mp4")
        video.audio_url = b2.upload(audio_path, f"{b2_prefix}_audio.wav")
        video.subtitle_url = b2.upload(srt_path, f"{b2_prefix}_captions.srt")
        video.captioned_video_url = b2.upload(captioned_path, f"{b2_prefix}_captioned.mp4")
    except Exception as e:
        pass

    video.status = "done"
    video.save()
