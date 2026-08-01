import os

from rest_framework import serializers

from .models import Video


class AudioExtractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            "id", "audio_file", "video_file", "captioned_video",
            "subtitle_file", "transcript", "caption_style", "status",
            "video_url", "audio_url", "captioned_video_url", "subtitle_url",
        ]
        read_only_fields = [
            "captioned_video", "subtitle_file", "transcript",
            "video_url", "audio_url", "captioned_video_url", "subtitle_url",
        ]

    def validate_video_file(self, value):
        allowed = [".mp4", ".mkv", ".avi", ".mov", ".webm"]
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed:
            raise serializers.ValidationError("File not supported")
        if value.size > 500 * 1024 * 1024:
            raise serializers.ValidationError("File too large")
        return value

    def validate_audio_file(self, value):
        if value and os.path.splitext(value.name)[1].lower() != ".wav":
            raise serializers.ValidationError("Audio must be a WAV file")
        return value
