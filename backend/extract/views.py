import json
import os
import uuid

from django.http import FileResponse
from rest_framework import status, views
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from . import b2
from .models import Video
from .processor import process_video
from .serializers import AudioExtractSerializer


class AudioExtractView(views.APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = AudioExtractSerializer(data=request.data)
        if serializer.is_valid():
            caption_style = request.data.get("caption_style")
            if isinstance(caption_style, str):
                caption_style = json.loads(caption_style)
            video = serializer.save(caption_style=caption_style or {})
            try:
                process_video(video.id)
                video.refresh_from_db()
                return Response(AudioExtractSerializer(video).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                video.status = "failed"
                video.save()
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CaptionedVideoUploadView(views.APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        f = request.FILES.get("file")
        if not f:
            return Response({"error": "file_required"}, status=status.HTTP_400_BAD_REQUEST)
        ext = os.path.splitext(f.name)[1].lower() or ".mp4"
        key = f"captioned/{uuid.uuid4().hex}{ext}"
        try:
            url = b2.upload_bytes(f.read(), key, content_type=f.content_type)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"key": key, "url": url})


class AudioStatusView(views.APIView):
    def get(self, request, pk):
        try:
            video = Video.objects.get(id=pk)
        except Video.DoesNotExist:
            return Response({"error": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        if video.status == "failed":
            return Response({"error": "processing_failed"}, status=status.HTTP_400_BAD_REQUEST)
        data = {"status": video.status, **AudioExtractSerializer(video).data}
        return Response(data)


class AudioDownloadView(views.APIView):
    def get(self, request, pk):
        try:
            video = Video.objects.get(id=pk)
        except Video.DoesNotExist:
            return Response({"error": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        field = request.query_params.get("type", "captioned_video")
        url = {
            "video": video.video_url,
            "audio": video.audio_url,
            "subtitle": video.subtitle_url,
            "captioned_video": video.captioned_video_url,
        }.get(field)
        if url:
            from urllib.parse import urlparse
            import urllib.request
            resp = urllib.request.urlopen(url)
            response = FileResponse(resp)
            response["Content-Disposition"] = f'attachment; filename="{os.path.basename(urlparse(url).path)}"'
            return response
        f = {
            "audio": video.audio_file,
            "subtitle": video.subtitle_file,
            "captioned_video": video.captioned_video,
        }.get(field)
        if f and os.path.exists(f.path):
            response = FileResponse(open(f.path, "rb"))
            response["Content-Disposition"] = f'attachment; filename="{os.path.basename(f.path)}"'
            return response
        return Response({"error": "file_not_found"}, status=status.HTTP_404_NOT_FOUND)
