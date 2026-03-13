from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import pytz

User = get_user_model()

SUPPORTED_LANGUAGES = ['en', 'ru', 'kk']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'preferred_language', 'timezone', 'avatar']
        read_only_fields = ['id', 'email']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    preferred_language = serializers.ChoiceField(
        choices=SUPPORTED_LANGUAGES, default='en', required=False
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'preferred_language']

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            preferred_language=validated_data.get('preferred_language', 'en'),
        )


class LanguageSerializer(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=SUPPORTED_LANGUAGES,
        error_messages={'invalid_choice': _("Unsupported language. Choose from: en, ru, kk.")}
    )


class TimezoneSerializer(serializers.Serializer):
    timezone = serializers.CharField()

    def validate_timezone(self, value):
        if value not in pytz.all_timezones_set:
            raise serializers.ValidationError(
                _("Invalid IANA timezone identifier: %(tz)s") % {"tz": value}
            )
        return value
