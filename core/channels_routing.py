from django.urls import re_path
from .channels_consumer import LoggerConsumer

websocket_urlpatterns = [
    re_path(r'^ws/notifications/(?P<logger>[\w.]+)/(?P<component>\w+)$', LoggerConsumer.as_asgi()),
]