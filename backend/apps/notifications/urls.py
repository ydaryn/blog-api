from django.urls import path
from apps.notifications.views import NotificationViewSet

v = NotificationViewSet.as_view

urlpatterns = [
    path("notifications/",       v({"get": "list"}),      name="notifications-list"),
    path("notifications/count/", v({"get": "count"}),     name="notifications-count"),
    path("notifications/read/",  v({"post": "mark_read"}), name="notifications-read"),
]