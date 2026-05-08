import os

from django.http import FileResponse
from rest_framework import status, views
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import Video
from .serializers import AudioExtractSerializer
from .tasks import audio_extract


class AudioExtractView(views.APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = AudioExtractSerializer(data=request.data)
        if serializer.is_valid():
            video_instance = serializer.save()
            audio_extract.delay(video_instance.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AudioStatusView(views.APIView):
    def get(self, request, pk):
        try:
            video = Video.objects.get(id=pk)
        except Video.DoesNotExist:
            return Response({"error": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        if video.status == "failed":
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if video.audio_file:
            return Response(
                {
                    "status": "done",
                    "audio_url": request.build_absolute_uri(video.audio_file.url),
                }
            )
        return Response({"status": "processing"})


class AudioDownloadView(views.APIView):
    def get(self, request, pk):
        video = Video.objects.get(id=pk)
        file_path = video.audio_file.path
        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = (
            f'attachment; filename="{os.path.basename(file_path)}"'
        )
