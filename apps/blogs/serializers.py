from rest_framework import serializers
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _
from django.utils.formats import date_format
import pytz

from .models import Post, Comment, Category, Tag


def _get_lang(request):
    if request:
        return getattr(request, 'LANGUAGE_CODE', 'en')[:2]
    return 'en'


def _format_datetime(dt, request):
    """Convert dt to user's timezone and format per locale."""
    if dt is None:
        return None
    user_tz = 'UTC'
    if request and request.user.is_authenticated:
        user_tz = getattr(request.user, 'timezone', 'UTC') or 'UTC'
    try:
        local_dt = dt.astimezone(pytz.timezone(user_tz))
    except Exception:
        local_dt = dt
    return local_dt.strftime('%d %B %Y %H:%M %Z')


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

    def get_name(self, obj):
        lang = _get_lang(self.context.get('request'))
        return obj.get_name(lang)


class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name_en', 'name_ru', 'name_kk', 'description']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class CommentSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_email', 'body', 'created_at']
        read_only_fields = ['id', 'author', 'author_email', 'created_at']

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("Comment body cannot be empty."))
        return value

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True,
        required=False, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', write_only=True,
        many=True, required=False
    )
    author_email = serializers.EmailField(source='author.email', read_only=True)
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'body', 'slug', 'author', 'author_email',
            'category', 'category_id', 'tags', 'tag_ids',
            'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'author', 'author_email', 'created_at', 'updated_at']

    def get_created_at(self, obj):
        return _format_datetime(obj.created_at, self.context.get('request'))

    def get_updated_at(self, obj):
        return _format_datetime(obj.updated_at, self.context.get('request'))

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("Title cannot be empty."))
        return value

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError(_("Post body cannot be empty."))
        return value

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
