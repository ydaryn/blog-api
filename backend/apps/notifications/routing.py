#python modules 
from django.urls import re_path

#project imports 
from apps.notifications.consumers import CommentConsumer

websocket_urlpatterns = [
    re_path(r"^ws/posts/(?P<slug>[\w-]+)/comments/$", CommentConsumer.as_asgi()),
]