import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # WebSocket routing will be added here when needed
    # "websocket": AuthMiddlewareStack(
    #     URLRouter([
    #         # WebSocket URL patterns
    #     ])
    # ),
})
