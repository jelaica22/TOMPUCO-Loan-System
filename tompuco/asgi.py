"""
ASGI config for tompuco project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# tompuco/asgi.py

import os
from django.core.asgi import get_asgi_application

# FIRST: Initialize Django ASGI application BEFORE importing consumers
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django_asgi_app = get_asgi_application()

# SECOND: Now import consumers (after Django is initialized)
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from committee import consumers

# WebSocket URL patterns
websocket_urlpatterns = [
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})