import os
import subprocess

from celery import shared_task

from .models import Video


@shared_task
def audio_extract(vid_id):

    try:
        input_video = Video.objects.get(id=vid_id)
    except Video.DoesNotExist:
        return f"Video {vid_id} not found"

    try:
        input_video_path = input_video.video_file.path
        output_video_filename = f"{os.path.splitext(input_video_path)[0]}.mp3"
        command = [
            "ffmpeg",
            "-i",
            input_video_path,
            "-vn",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            output_video_filename,
        ]
        subprocess.run(command, check=True)
        input_video.audio_file = output_video_filename.replace("/app/media/", "")
        input_video.status = "done"
        input_video.save()
        return f"extracted to {output_video_filename}"
    except Exception as e:
        input_video.status = "failed"
        input_video.save()
        return f"Error{e}"
