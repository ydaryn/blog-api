from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserCreateView, UserDetailView, LanguageUpdateView, TimezoneUpdateView

urlpatterns = [
    path('register/', UserCreateView.as_view(), name='user-register'),
    path('me/', UserDetailView.as_view(), name='user-me'),
    path('language/', LanguageUpdateView.as_view(), name='user-language'),
    path('timezone/', TimezoneUpdateView.as_view(), name='user-timezone'),
    path('token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
