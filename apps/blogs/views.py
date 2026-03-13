import asyncio
import json
import logging

import httpx
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
    extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse
)

from .models import Post, Comment, Category, Tag
from .serializers import (
    PostSerializer, CommentSerializer,
    CategorySerializer, CategoryWriteSerializer, TagSerializer,
)
from .permissions import IsAuthorOrReadOnly

logger = logging.getLogger("apps.blogs")

POSTS_CACHE_TIMEOUT = 60 * 5  # 5 minutes


def _posts_cache_key(request):
    lang = getattr(request, 'LANGUAGE_CODE', 'en')[:2]
    page = request.GET.get('page', '1')
    status_filter = request.GET.get('status', '')
    return f"posts_list:lang={lang}:page={page}:status={status_filter}"


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author', 'category').prefetch_related('tags')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'body', 'author__email']
    ordering_fields = ['created_at', 'updated_at', 'title']

    @extend_schema(
        tags=["Posts"],
        summary="List published posts",
        description=(
            "Returns a paginated list of posts. Results are cached in Redis per language "
            "and per page. Cache is invalidated on any write (create, update, delete). "
            "Dates are formatted according to the user's locale and converted to their timezone."
        ),
        parameters=[
            OpenApiParameter("lang", str, description="Override language (en/ru/kk)"),
            OpenApiParameter("status", str, description="Filter by status (draft/published)"),
            OpenApiParameter("search", str, description="Search in title, body, author email"),
        ],
        responses={200: PostSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Post list response",
                value={"count": 2, "results": [
                    {"id": 1, "title": "Hello World", "slug": "hello-world",
                     "status": "published", "created_at": "13 March 2026 14:00 UTC"}
                ]},
                response_only=True, status_codes=["200"],
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        cache_key = _posts_cache_key(request)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, POSTS_CACHE_TIMEOUT)
        return response

    @extend_schema(tags=["Posts"], summary="Create a post",
                   description="Creates a new post. Requires authentication. Invalidates posts list cache for all languages.",
                   responses={201: PostSerializer, 400: OpenApiResponse(description="Validation error"), 401: OpenApiResponse(description="Unauthenticated")})
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self._invalidate_posts_cache()
        return response

    @extend_schema(tags=["Posts"], summary="Retrieve a post",
                   responses={200: PostSerializer, 404: OpenApiResponse(description="Not found")})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Update a post",
                   description="Full update. Only the post author can update. Invalidates posts list cache.",
                   responses={200: PostSerializer, 400: OpenApiResponse(description="Validation error"),
                               401: OpenApiResponse(description="Unauthenticated"), 403: OpenApiResponse(description="Forbidden")})
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self._invalidate_posts_cache()
        return response

    @extend_schema(tags=["Posts"], summary="Partial update a post",
                   responses={200: PostSerializer, 403: OpenApiResponse(description="Forbidden")})
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        self._invalidate_posts_cache()
        return response

    @extend_schema(tags=["Posts"], summary="Delete a post",
                   description="Only the post author can delete. Invalidates posts list cache.",
                   responses={204: None, 403: OpenApiResponse(description="Forbidden")})
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        self._invalidate_posts_cache()
        return response

    def _invalidate_posts_cache(self):
        """Delete cached post list for all languages so every user gets fresh data."""
        for lang in ['en', 'ru', 'kk']:
            # Invalidate first 20 pages per language to be safe
            for page in range(1, 21):
                for status_val in ['', 'draft', 'published']:
                    key = f"posts_list:lang={lang}:page={page}:status={status_val}"
                    cache.delete(key)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author', 'post')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    @extend_schema(tags=["Comments"], summary="List comments",
                   description="List all comments. Filter by post via ?post=<id>.",
                   responses={200: CommentSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Comments"], summary="Create a comment",
                   description=(
                       "Post a comment. Requires authentication. "
                       "Publishes a JSON event to Redis channel 'new_comments' "
                       "with post slug, author id, and comment body."
                   ),
                   responses={201: CommentSerializer, 400: OpenApiResponse(description="Validation error"),
                               401: OpenApiResponse(description="Unauthenticated")},
                   examples=[
                       OpenApiExample("Request", value={"post": 1, "body": "Great post!"},
                                      request_only=True),
                       OpenApiExample("Response",
                                      value={"id": 5, "post": 1, "author": 2,
                                             "author_email": "bob@example.com",
                                             "body": "Great post!", "created_at": "2026-03-13T14:00:00Z"},
                                      response_only=True, status_codes=["201"]),
                   ])
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            self._publish_comment_event(response.data)
        return response

    def _publish_comment_event(self, comment_data):
        try:
            import redis as redis_lib
            from django.conf import settings as django_settings
            r = redis_lib.Redis(
                host=django_settings.REDIS_HOST,
                port=django_settings.REDIS_PORT,
                db=0,
            )
            # Find post slug
            try:
                post = Post.objects.get(pk=comment_data['post'])
                slug = post.slug
            except Post.DoesNotExist:
                slug = str(comment_data['post'])
            event = json.dumps({
                "post_slug": slug,
                "author_id": comment_data['author'],
                "body": comment_data['body'],
            })
            r.publish("new_comments", event)
        except Exception as exc:
            logger.warning("Failed to publish comment event: %s", exc)

    @extend_schema(tags=["Comments"], summary="Retrieve a comment",
                   responses={200: CommentSerializer, 404: OpenApiResponse(description="Not found")})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Comments"], summary="Update a comment",
                   responses={200: CommentSerializer, 403: OpenApiResponse(description="Forbidden")})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Comments"], summary="Partial update a comment",
                   responses={200: CommentSerializer, 403: OpenApiResponse(description="Forbidden")})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Comments"], summary="Delete a comment",
                   responses={204: None, 403: OpenApiResponse(description="Forbidden")})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        post_id = self.request.query_params.get('post')
        if post_id:
            qs = qs.filter(post_id=post_id)
        return qs


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return CategoryWriteSerializer
        return CategorySerializer

    @extend_schema(tags=["Posts"], summary="List categories",
                   description="Returns categories with names in the active language.",
                   responses={200: CategorySerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Create a category",
                   description="Create a category with per-language names.",
                   responses={201: CategoryWriteSerializer, 400: OpenApiResponse(description="Validation error")})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Retrieve a category", responses={200: CategorySerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Update a category", responses={200: CategoryWriteSerializer})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Partial update a category", responses={200: CategoryWriteSerializer})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Delete a category", responses={204: None})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(tags=["Posts"], summary="List tags", responses={200: TagSerializer(many=True)})
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Create a tag",
                   responses={201: TagSerializer, 400: OpenApiResponse(description="Validation error")})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Retrieve a tag", responses={200: TagSerializer})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Update a tag", responses={200: TagSerializer})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Partial update a tag", responses={200: TagSerializer})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["Posts"], summary="Delete a tag", responses={204: None})
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# ─── Stats View (Async) ───────────────────────────────────────────────────────

class StatsView(APIView):
    """
    Async view: we call two external APIs concurrently with asyncio.gather.
    If this were synchronous, the two HTTP calls would execute sequentially,
    making total latency = sum of both call times instead of max of both.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Stats"],
        summary="Get blog statistics and external data",
        description=(
            "Returns blog counts combined with live exchange rates and current Almaty time. "
            "The two external API calls (open.er-api.com and timeapi.io) happen concurrently "
            "via asyncio.gather — total latency equals the slower of the two, not their sum. "
            "No authentication required."
        ),
        responses={
            200: OpenApiResponse(description="Stats response"),
            503: OpenApiResponse(description="External API unavailable"),
        },
        examples=[
            OpenApiExample(
                "Stats response",
                value={
                    "blog": {"total_posts": 42, "total_comments": 137, "total_users": 15},
                    "exchange_rates": {"KZT": 450.23, "RUB": 89.10, "EUR": 0.92},
                    "current_time": "2026-03-13T18:30:00+05:00",
                },
                response_only=True, status_codes=["200"],
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        # Run the async logic from within the sync WSGI context.
        data = asyncio.run(self._gather_stats())
        return Response(data)

    async def _gather_stats(self):
        from apps.users.models import User
        from .models import Post, Comment
        from asgiref.sync import sync_to_async

        # Fetch DB counts and both external APIs concurrently.
        db_counts, exchange_rates, current_time = await asyncio.gather(
            sync_to_async(self._get_db_counts)(),
            self._fetch_exchange_rates(),
            self._fetch_current_time(),
        )
        return {
            "blog": db_counts,
            "exchange_rates": exchange_rates,
            "current_time": current_time,
        }

    def _get_db_counts(self):
        from apps.users.models import User
        return {
            "total_posts": Post.objects.count(),
            "total_comments": Comment.objects.count(),
            "total_users": User.objects.count(),
        }

    async def _fetch_exchange_rates(self):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://open.er-api.com/v6/latest/USD")
                resp.raise_for_status()
                rates = resp.json().get("rates", {})
                return {k: rates[k] for k in ("KZT", "RUB", "EUR") if k in rates}
        except Exception as exc:
            logger.warning("Exchange rate fetch failed: %s", exc)
            return {"KZT": None, "RUB": None, "EUR": None}

    async def _fetch_current_time(self):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://timeapi.io/api/time/current/zone",
                    params={"timeZone": "Asia/Almaty"},
                )
                resp.raise_for_status()
                return resp.json().get("dateTime")
        except Exception as exc:
            logger.warning("Time API fetch failed: %s", exc)
            return None
