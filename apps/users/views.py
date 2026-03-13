from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from .serializers import (
    UserSerializer, UserCreateSerializer,
    LanguageSerializer, TimezoneSerializer,
)

User = get_user_model()


class UserCreateView(generics.CreateAPIView):
    """Register a new user. Sends a welcome email in the user's preferred language."""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Register a new user",
        description=(
            "Creates a new user account. Sends a welcome email rendered from a template "
            "in the language the user selected at registration, independent of the active "
            "request language. No authentication required."
        ),
        request=UserCreateSerializer,
        responses={201: UserSerializer, 400: OpenApiResponse(description="Validation error")},
        examples=[
            OpenApiExample(
                "Register request",
                value={"email": "alice@example.com", "first_name": "Alice",
                       "last_name": "Smith", "password": "secret123", "preferred_language": "ru"},
                request_only=True,
            ),
            OpenApiExample(
                "Register response",
                value={"id": 1, "email": "alice@example.com", "first_name": "Alice",
                       "last_name": "Smith", "preferred_language": "ru", "timezone": "UTC"},
                response_only=True, status_codes=["201"],
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        self._send_welcome_email(user)
        out = UserSerializer(user, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def _send_welcome_email(self, user):
        lang = user.preferred_language or "en"
        # Activate user's language for rendering the email — independent of request language.
        with translation.override(lang):
            subject = render_to_string("emails/welcome/subject.txt", {"user": user}).strip()
            body = render_to_string("emails/welcome/body.txt", {"user": user})
        send_mail(subject, body, "noreply@blog.local", [user.email], fail_silently=False)


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Get or update current user",
        description="Retrieve or partially update the authenticated user's profile.",
        responses={200: UserSerializer},
    )
    def get_object(self):
        return self.request.user


class LanguageUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Set preferred language",
        description=(
            "Updates the authenticated user's preferred language. "
            "Valid values: en, ru, kk. Returns 400 for unknown codes. "
            "The new language is used on all subsequent requests for this user."
        ),
        request=LanguageSerializer,
        responses={
            200: OpenApiResponse(description="Language updated"),
            400: OpenApiResponse(description="Invalid language code"),
        },
        examples=[
            OpenApiExample("Request", value={"language": "ru"}, request_only=True),
            OpenApiExample("Response", value={"detail": "Language updated to ru"},
                           response_only=True, status_codes=["200"]),
        ],
    )
    def patch(self, request, *args, **kwargs):
        serializer = LanguageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lang = serializer.validated_data["language"]
        request.user.preferred_language = lang
        request.user.save(update_fields=["preferred_language"])
        return Response({"detail": str(_("Language updated to %(lang)s") % {"lang": lang})})


class TimezoneUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Set preferred timezone",
        description=(
            "Updates the authenticated user's timezone. Must be a valid IANA timezone string "
            "(e.g. Asia/Almaty, Europe/Moscow). Returns 400 with a clear error if invalid. "
            "Post dates in list/detail responses will be converted to this timezone."
        ),
        request=TimezoneSerializer,
        responses={
            200: OpenApiResponse(description="Timezone updated"),
            400: OpenApiResponse(description="Invalid IANA timezone"),
        },
        examples=[
            OpenApiExample("Request", value={"timezone": "Asia/Almaty"}, request_only=True),
            OpenApiExample("Response", value={"detail": "Timezone updated to Asia/Almaty"},
                           response_only=True, status_codes=["200"]),
        ],
    )
    def patch(self, request, *args, **kwargs):
        serializer = TimezoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tz = serializer.validated_data["timezone"]
        request.user.timezone = tz
        request.user.save(update_fields=["timezone"])
        return Response({"detail": str(_("Timezone updated to %(tz)s") % {"tz": tz})})
