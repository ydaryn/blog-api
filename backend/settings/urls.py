#Django modules
from django.contrib import admin
from django.urls import path, include

# Third-party modules
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


# Project modules
from apps.blog.views_async import StatsView
from apps.blog.views_async import post_stream

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.users.auth.urls")),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.blog.urls")),
    path("api/stats/", StatsView.as_view(), name="stats"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/posts/stream/",post_stream,name="post-stream"),
    path("api/", include("apps.notifications.urls")),

]
