from rest_framework import serializers

from .models import Video


class AudioExtractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["video_file", "id", "audio_file"]
        read_only_fields = ["audio_file"]
