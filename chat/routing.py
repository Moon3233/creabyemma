"""Routing WebSocket pour le chat."""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/chat/admin/", consumers.ChatConsumer.as_asgi()),
    path("ws/chat/<str:guest_token>/", consumers.ChatConsumer.as_asgi()),
]
