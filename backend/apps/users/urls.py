from rest_framework.routers import DefaultRouter

from django.urls import path, include

from apps.users.views import CustomUserViewSet

router = DefaultRouter()
router.register(r"", CustomUserViewSet, basename="")

urlpatterns = [
    path("user/", include(router.urls)),
]
