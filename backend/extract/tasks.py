import os
import subprocess

from celery import shared_task

from .models import Video


@shared_task
def audio_extract(vid_id):
    try:
        input_video = Video.object.get(id=vid_id)
        input_video_path = input_video.video_file.path
        output_video_filename = f"{os.path.splitext(input_video_path)[0]}.mp3"
        command = [
            "ffmpeg",
            "-i",
            input_video_path,
            "-vn",
            ",-c:a",
            "copy",
            output_video_filename,
        ]
        subprocess.run(command, check=True)
        return f"extracted to {output_video_filename}"
    except Exception as e:
        return f"Error{e}"
