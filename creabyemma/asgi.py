"""
ASGI config for creabyemma project.
HTTP + WebSocket (chat).
"""

import os
import warnings

warnings.filterwarnings(
    "ignore",
    message="StreamingHttpResponse must consume synchronous iterators",
)

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creabyemma.settings')

django_asgi_app = get_asgi_application()

from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import OriginValidator
from chat.routing import websocket_urlpatterns

_ws_origins = list(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))
if not _ws_origins:
    _ws_origins = ['http://localhost:5173', 'http://127.0.0.1:5173']
for o in ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:8000', 'http://127.0.0.1:8000']:
    if o not in _ws_origins:
        _ws_origins.append(o)

ws_app = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
ws_final = OriginValidator(ws_app, _ws_origins) if not settings.DEBUG else ws_app
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': ws_final,
})
