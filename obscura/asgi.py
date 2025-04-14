# obscura/asgi.py
import os
from django.core.asgi import get_asgi_application

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obscura.settings')

# Initialize Django
django_asgi_app = get_asgi_application()

# Import after Django is set up
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})