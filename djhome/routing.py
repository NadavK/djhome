from channels.routing import ProtocolTypeRouter, URLRouter
import ios.routing
from djhome.json_token_auth import JsonTokenAuthMiddlewareStack


# Define Daphne routing
# djhome only expects WebSocket connections from Daphne

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': JsonTokenAuthMiddlewareStack(
        URLRouter(
            ios.routing.websocket_urlpatterns
        )
    ),
})
