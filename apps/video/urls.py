from django.urls import path

from apps.video import views

urlpatterns = [
    # urls.py
    path("video/<str:filename>", views.stream_video, name="stream-video"),

    path("test/", views.video_player, name="video-player")
]
