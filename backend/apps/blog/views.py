# Python modules
from typing import Any
import logging

# Project tasks
from apps.blog.tasks import invalidate_posts_cache
from apps.notifications.tasks import process_new_comment

# Third-party modules
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response as DRFResponse
from rest_framework.request import Request as DRFRequest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

# Django modules
from django.db.models import Q
from django.core.cache import cache
import redis as sync_redis
from django.conf import settings


# Project modules
from apps.blog.models import Post, Comment
from apps.blog.serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer,
    CommentSerializer,
)
from apps.blog.permissions import IsAuthorOrReadOnly
from apps.abstract.pagination import DefaultPagination
from apps.abstract.ratelimit import ratelimit

logger = logging.getLogger(__name__)


class PostViewSet(ViewSet):  # noqa
    """
    ViewSet for Post model:
    - GET /api/posts/ — List published posts (no auth required)
    - POST /api/posts/ — Create post (auth required)
    - GET /api/posts/{slug}/ — Get single post (no auth required)
    - PATCH /api/posts/{slug}/ — Update own post (auth required)
    - DELETE /api/posts/{slug}/ — Delete own post (auth required)
    - GET /api/posts/{slug}/comments/ — List comments (no auth required)
    - POST /api/posts/{slug}/comments/ — Add comment (auth required)
    """

    lookup_field: str = "slug"
    permission_classes: tuple = (IsAuthorOrReadOnly,)
    pagination_class = DefaultPagination

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def check_permissions(self, request):
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                raise PermissionDenied()

    def check_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                raise PermissionDenied()

    @extend_schema(
        summary="List posts",
        description="Returns list of published posts. Authenticated users also see their own drafts. Response is cached per language. Cache invalidated on any post write.",
        tags=["Posts"],
        parameters=[
            OpenApiParameter("lang", OpenApiTypes.STR, description="Language code: en, ru, kk"),
        ],
        responses={
            200: PostListSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
        },
        examples=[
            OpenApiExample(
                "Posts list response",
                value={"results": [{"id": 1, "title": "Test Post", "slug": "test-post", "status": "published", "created_at": "03:57 14 марта 2026"}]},
                response_only=True,
            ),
        ],
    )
    def list(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        user_info = (
            f"user_id={request.user.id}"
            if request.user.is_authenticated
            else "anonymous"
        )
        logger.info(f"Listing posts requested by {user_info}")

        if request.user.is_authenticated:
            queryset = Post.objects.filter(
                Q(status=Post.Status.PUBLISHED) | Q(author=request.user)
            )
            logger.debug(f"Posts queryset count: {queryset.count()} for {user_info}")

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, view=self)

            if page is not None:
                serializer: PostListSerializer = PostListSerializer(page, many=True, context={'request': request})
                return paginator.get_paginated_response(serializer.data)

            serializer: PostListSerializer = PostListSerializer(queryset, many=True, context={'request': request})
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK,
            )

        lang = getattr(request, "LANGUAGE_CODE", "en")
        cache_key = f"published_posts_list_{lang}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            logger.info(f"Returning cached posts list for {user_info}")
            return DRFResponse(
                data=cached_data,
                status=HTTP_200_OK,
            )

        logger.info(f"Cache miss - fetching posts from database for {user_info}")
        queryset = Post.objects.filter(status=Post.Status.PUBLISHED)
        logger.debug(f"Posts queryset count: {queryset.count()} for {user_info}")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer: PostListSerializer = PostListSerializer(page, many=True, context={'request': request})
            response_data = paginator.get_paginated_response(serializer.data).data
            cache.set(cache_key, response_data, 60)
            logger.info("Cached posts list for 60 seconds")
            return DRFResponse(
                data=response_data,
                status=HTTP_200_OK,
            )

        serializer: PostListSerializer = PostListSerializer(queryset, many=True, context={'request': request})
        response_data = serializer.data
        cache.set(cache_key, response_data, 60)
        logger.info("Cached posts list for 60 seconds")
        return DRFResponse(
            data=response_data,
            status=HTTP_200_OK,
        )

    @extend_schema(
        summary="Create post",
        description="Create a new post. Authentication required. Invalidates posts cache for all languages.",
        tags=["Posts"],
        request=PostCreateUpdateSerializer,
        responses={
            201: PostCreateUpdateSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            429: OpenApiResponse(description="Too many requests"),
        },
        examples=[
            OpenApiExample(
                "Create post example",
                value={"title": "My Post", "body": "Post content here", "status": "published"},
                request_only=True,
            ),
        ],
    )
    @ratelimit(key_func=lambda r: str(r.user.id) if r.user.is_authenticated else "anonymous", rate="20/m", method="POST")
    def create(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning("Unauthorized attempt to create post")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Creating post by user_id={request.user.id}")

        serializer: PostCreateUpdateSerializer = PostCreateUpdateSerializer(
            data=request.data,
        )

        if serializer.is_valid():
            post = serializer.save(author=request.user)

            if post.status == Post.Status.PUBLISHED:
                r = sync_redis.from_url(settings.REDIS_URL)
                r.publish("post_published", json.dumps({
                    "post_id": post.id,
                    "title": post.title,
                    "slug": post.slug,
                    "author": {"id": post.author.id, "email": post.author.email},
                    "published_at": post.updated_at.isoformat(),
                }))
                r.close()

            invalidate_posts_cache.delay()
            logger.info("Invalidated published posts cache after post creation")

            logger.info(
                f"Post created successfully: post_id={post.id}, "
                f"slug={post.slug}, author_id={request.user.id}"
            )
            return DRFResponse(
                data=serializer.data,
                status=HTTP_201_CREATED,
            )

        logger.error(
            f"Post creation failed for user_id={request.user.id}: {serializer.errors}"
        )
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        summary="Get post",
        description="Get single post by slug. No authentication required. Dates formatted per user locale and timezone.",
        tags=["Posts"],
        responses={
            200: PostDetailSerializer,
            404: OpenApiResponse(description="Post not found"),
        },
        examples=[
            OpenApiExample(
                "Post detail response",
                value={"id": 1, "title": "Test Post", "slug": "test-post", "body": "Post content", "status": "published", "created_at": "03:57 14 марта 2026", "updated_at": "03:57 14 марта 2026"},
                response_only=True,
            ),
        ],
    )
    def retrieve(
        self,
        request: DRFRequest,
        slug: str = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        logger.info(f"Retrieving post with slug={slug}")

        try:
            post: Post = Post.objects.get(slug=slug)
            logger.info(f"Post retrieved: post_id={post.id}, slug={slug}")
        except Post.DoesNotExist:
            logger.warning(f"Post not found: slug={slug}")
            raise NotFound(detail="Post not found")

        serializer: PostDetailSerializer = PostDetailSerializer(post, context={'request': request})
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
        )

    @extend_schema(
        summary="Update post",
        description="Partially update a post. Only the author can update. Invalidates cache for all languages.",
        tags=["Posts"],
        request=PostCreateUpdateSerializer,
        responses={
            200: PostCreateUpdateSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Not the author"),
            404: OpenApiResponse(description="Post not found"),
        },
    )
    def partial_update(
        self,
        request: DRFRequest,
        slug: str = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized attempt to update post with slug={slug}")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Updating post: slug={slug}, user_id={request.user.id}")

        try:
            post: Post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            logger.warning(f"Post not found for update: slug={slug}")
            raise NotFound(detail="Post not found")

        self.check_object_permissions(request, post)

        serializer: PostCreateUpdateSerializer = PostCreateUpdateSerializer(
            post,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            if post.status == Post.Status.PUBLISHED:
                r = sync_redis.from_url(settings.REDIS_URL)
                r.publish("post_published", json.dumps({
                    "post_id": post.id,
                    "title": post.title,
                    "slug": post.slug,
                    "author": {"id": post.author.id, "email": post.author.email},
                    "published_at": post.updated_at.isoformat(),
                }))
                r.close()

            invalidate_posts_cache.delay()
            logger.info("Invalidated published posts cache after post update")

            logger.info(
                f"Post updated successfully: post_id={post.id}, "
                f"slug={slug}, user_id={request.user.id}"
            )
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK,
            )

        logger.error(
            f"Post update failed: post_id={post.id}, "
            f"user_id={request.user.id}, errors={serializer.errors}"
        )
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        summary="Delete post",
        description="Delete a post. Only the author can delete. Invalidates cache for all languages.",
        tags=["Posts"],
        responses={
            204: OpenApiResponse(description="Post deleted"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Not the author"),
            404: OpenApiResponse(description="Post not found"),
        },
    )
    def destroy(
        self,
        request: DRFRequest,
        slug: str = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized attempt to delete post with slug={slug}")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Deleting post: slug={slug}, user_id={request.user.id}")

        try:
            post: Post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            logger.warning(f"Post not found for deletion: slug={slug}")
            raise NotFound(detail="Post not found")

        self.check_object_permissions(request, post)

        post_id = post.id
        post.delete()

        invalidate_posts_cache.delay()
        logger.info("Invalidated published posts cache after post deletion")

        logger.info(
            f"Post deleted successfully: post_id={post_id}, "
            f"slug={slug}, user_id={request.user.id}"
        )
        return DRFResponse(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="List or create comments for a post",
        description="GET: list comments for a post, no auth required. POST: add comment, auth required. Comment event published to Redis on creation.",
        tags=["Posts"],
        request=CommentSerializer,
        responses={
            200: CommentSerializer(many=True),
            201: CommentSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Post not found"),
        },
    )
    @action(
        detail=True,
        methods=("GET", "POST"),
        url_path="comments",
        url_name="comments",
        permission_classes=(AllowAny,),
    )
    def comments(
        self,
        request: DRFRequest,
        slug: str = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        logger.info(f"Comments action: method={request.method}, slug={slug}")

        try:
            post: Post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            logger.warning(f"Post not found for comments: slug={slug}")
            raise NotFound(detail="Post not found")

        if request.method == "GET":
            logger.info(f"Listing comments for post: post_id={post.id}, slug={slug}")

            comments_qs = post.comments.all().order_by("-created_at")

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(comments_qs, request, view=self)

            if page is not None:
                serializer: CommentSerializer = CommentSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer: CommentSerializer = CommentSerializer(comments_qs, many=True)
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK,
            )

        elif request.method == "POST":
            if not request.user.is_authenticated:
                logger.warning(
                    f"Unauthorized attempt to comment on post: post_id={post.id}"
                )
                return DRFResponse(
                    data={"detail": "Authentication required to post comments."},
                    status=HTTP_401_UNAUTHORIZED,
                )

            logger.info(
                f"Creating comment: post_id={post.id}, user_id={request.user.id}"
            )

            serializer: CommentSerializer = CommentSerializer(data=request.data)

            if serializer.is_valid():
                comment = serializer.save(author=request.user, post=post)
                process_new_comment.delay(comment.id)

                
                logger.info(
                    f"Comment created successfully: comment_id={comment.id}, "
                    f"post_id={post.id}, user_id={request.user.id}"
                )
                return DRFResponse(
                    data=serializer.data,
                    status=HTTP_201_CREATED,
                )

            logger.error(
                f"Comment creation failed: post_id={post.id}, "
                f"user_id={request.user.id}, errors={serializer.errors}"
            )
            return DRFResponse(
                data=serializer.errors,
                status=HTTP_400_BAD_REQUEST,
            )


class CommentViewSet(ViewSet):
    permission_classes: tuple = (IsAuthorOrReadOnly,)
    pagination_class = DefaultPagination

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def check_permissions(self, request):
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                raise PermissionDenied()

    def check_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                raise PermissionDenied()

    @extend_schema(
        summary="List all comments",
        description="Returns all comments across all posts. No authentication required.",
        tags=["Comments"],
        responses={200: CommentSerializer(many=True)},
    )
    def list(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        logger.info("Listing all comments")

        queryset = Comment.objects.all().order_by("-created_at")
        logger.debug(f"Total comments count: {queryset.count()}")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer: CommentSerializer = CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer: CommentSerializer = CommentSerializer(queryset, many=True)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
        )

    @extend_schema(
        summary="Get comment",
        description="Get single comment by ID.",
        tags=["Comments"],
        responses={
            200: CommentSerializer,
            404: OpenApiResponse(description="Comment not found"),
        },
    )
    def retrieve(
        self,
        request: DRFRequest,
        pk: int = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        logger.info(f"Retrieving comment with pk={pk}")

        try:
            comment: Comment = Comment.objects.get(pk=pk)
            logger.info(f"Comment retrieved: comment_id={comment.id}")
        except Comment.DoesNotExist:
            logger.warning(f"Comment not found: pk={pk}")
            raise NotFound(detail="Comment not found")

        serializer: CommentSerializer = CommentSerializer(comment)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_200_OK,
        )

    @extend_schema(
        summary="Update comment",
        description="Partially update a comment. Only the author can update.",
        tags=["Comments"],
        request=CommentSerializer,
        responses={
            200: CommentSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Not the author"),
            404: OpenApiResponse(description="Comment not found"),
        },
    )
    def partial_update(
        self,
        request: DRFRequest,
        pk: int = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized attempt to update comment with pk={pk}")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Updating comment: pk={pk}, user_id={request.user.id}")

        try:
            comment: Comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            logger.warning(f"Comment not found for update: pk={pk}")
            raise NotFound(detail="Comment not found")

        self.check_object_permissions(request, comment)

        serializer: CommentSerializer = CommentSerializer(
            comment,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            logger.info(
                f"Comment updated successfully: comment_id={comment.id}, "
                f"user_id={request.user.id}"
            )
            return DRFResponse(
                data=serializer.data,
                status=HTTP_200_OK,
            )

        logger.error(
            f"Comment update failed: comment_id={comment.id}, "
            f"user_id={request.user.id}, errors={serializer.errors}"
        )
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        summary="Delete comment",
        description="Delete a comment. Only the author can delete.",
        tags=["Comments"],
        responses={
            204: OpenApiResponse(description="Comment deleted"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Not the author"),
            404: OpenApiResponse(description="Comment not found"),
        },
    )
    def destroy(
        self,
        request: DRFRequest,
        pk: int = None,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        self.check_permissions(request)

        if not request.user.is_authenticated:
            logger.warning(f"Unauthorized attempt to delete comment with pk={pk}")
            return DRFResponse(
                data={"detail": "Authentication required."},
                status=HTTP_401_UNAUTHORIZED,
            )

        logger.info(f"Deleting comment: pk={pk}, user_id={request.user.id}")

        try:
            comment: Comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            logger.warning(f"Comment not found for deletion: pk={pk}")
            raise NotFound(detail="Comment not found")

        self.check_object_permissions(request, comment)

        comment_id = comment.id
        comment.delete()

        logger.info(
            f"Comment deleted successfully: comment_id={comment_id}, "
            f"user_id={request.user.id}"
        )
        return DRFResponse(status=HTTP_204_NO_CONTENT)