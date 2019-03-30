from django.conf.urls import url
#from ios.consumers import Demultiplexer
from . import consumers


websocket_urlpatterns = [
    url(r'^io/$', consumers.IOConsumer),
]