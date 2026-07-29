import json
import os
import subprocess

import requests
from celery import shared_task
from django.conf import settings

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
    """Split long segments into smaller chunks (max_words per subtitle)."""
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


@shared_task
def generate_captions(vid_id):
    try:
        video = Video.objects.get(id=vid_id)
    except Video.DoesNotExist:
        return f"Video {vid_id} not found"

    api_key = os.environ.get("SARVAM_API_KEY", "")
    if not api_key:
        video.status = "failed"
        video.save()
        return "SARVAM_API_KEY not set"

    try:
        video_path = video.video_file.path
        media_root = settings.MEDIA_ROOT
        video_dir = os.path.dirname(video_path)
        base = os.path.splitext(os.path.basename(video_path))[0]

        audio_path = os.path.join(video_dir, f"{base}_audio.wav")
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", audio_path, "-y"],
            check=True, capture_output=True,
        )
        video.audio_file = os.path.relpath(audio_path, media_root)
        video.save()

        dur = float(
            subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", audio_path],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
        )

        all_segments = []
        if dur <= 28:
            all_segments = _transcribe(api_key, audio_path)
        else:
            import glob
            import tempfile
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

        video.transcript = all_segments
        video.save()

        srt_path = os.path.join(video_dir, f"{base}.srt")
        _write_srt(all_segments, srt_path)
        video.subtitle_file = os.path.relpath(srt_path, media_root)
        video.save()

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
             f"PrimaryColour={color},"
             f"OutlineColour={bg},"
             f"BackColour=&H{int(bg_op*255):02X}000000,"
             f"BorderStyle=1,Outline=2,Shadow=1,"
             f"Alignment=2,MarginV={mv}'",
             "-c:a", "aac", "-b:a", "192k",
             "-preset", "fast", captioned_path, "-y"],
            check=True, capture_output=True,
        )

        video.captioned_video = os.path.relpath(captioned_path, media_root)
        video.status = "done"
        video.save()
        return f"Captions generated for {base}"
    except Exception as e:
        video.status = "failed"
        video.save()
        return f"Error: {e}"
