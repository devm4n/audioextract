import os

from rest_framework import serializers

from .models import Video


class AudioExtractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["id", "audio_file", "video_file", "status"]
        read_only_fields = ["audio_file"]

    def validate_video_file(self, value):
        allowed = [".mp4", ".mkv", ".avi", ".mov", ".webm"]
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed:
            raise serializers.ValidationError("File not supported")
        if value.size > 500 * 1024 * 1024:
            raise serializers.ValidationError("File too large")
        return value
