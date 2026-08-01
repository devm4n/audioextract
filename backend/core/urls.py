from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from extract import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/upload/", views.AudioExtractView.as_view()),
    path("upload/", views.AudioExtractView.as_view()),
    path("api/status/<int:pk>/", views.AudioStatusView.as_view()),
    path("status/<int:pk>/", views.AudioStatusView.as_view()),
    path("api/download/<int:pk>/", views.AudioDownloadView.as_view()),
    path("download/<int:pk>/", views.AudioDownloadView.as_view()),
    path("api/finalize/", views.CaptionedVideoUploadView.as_view()),
    path("finalize/", views.CaptionedVideoUploadView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
