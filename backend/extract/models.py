from django.db import models


class Video(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(upload_to="video/%d/%m/%Y")

    def __str__(self):
        return self.create_at
