from django.db import models


class Video(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(upload_to="video/%d/%m/%Y")
    audio_file = models.FileField(null=True, blank=True)
