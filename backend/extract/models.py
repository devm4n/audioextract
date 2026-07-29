from django.db import models


class Video(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(upload_to="video/%d/%m/%Y")
    audio_file = models.FileField(null=True, blank=True)
    captioned_video = models.FileField(null=True, blank=True)
    subtitle_file = models.FileField(null=True, blank=True)
    transcript = models.JSONField(null=True, blank=True)
    caption_style = models.JSONField(default=dict, blank=True)
    status = models.CharField(default="processing")
    video_url = models.URLField(null=True, blank=True, max_length=2000)
    audio_url = models.URLField(null=True, blank=True, max_length=2000)
    captioned_video_url = models.URLField(null=True, blank=True, max_length=2000)
    subtitle_url = models.URLField(null=True, blank=True, max_length=2000)
