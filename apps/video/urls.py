from django.urls import path

from apps.video import views

app_name = "video"


urlpatterns = [
    path("video/<str:filename>", views.stream_video, name="stream-video"),
    path("test/", views.video_player, name="video-player"),
]
