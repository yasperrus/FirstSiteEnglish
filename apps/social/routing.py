from django.urls import path
from apps.social.consumers import LikesConsumer

websocket_urlpatterns = [
    path("ws/likes/", LikesConsumer.as_asgi()),
]
