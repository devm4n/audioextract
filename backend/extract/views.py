from rest_framework import status, views
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from tasks import audio_extract

from .serializers import AudioExtractSerializer


class AudioExtractView(views.APIView):
    def post(self, request):
        parser_classes = (MultiPartParser, FormParser)
        serializer = AudioExtractSerializer(data=request.data)
        if serializer.is_valid():
            video_instanace = serializer.save()
            audio_extract.delay(video_instanace.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_501_NOT_IMPLEMENTED)
