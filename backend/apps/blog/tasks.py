from celery import shared_task
from django.utils import timezone
import logging, json

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(Exception,),retry_backoff=True,max_retries=3)
def invalidate_posts_cache()->None:
    from django.core.cache import cache
    cache.delete_pattern("posts_list_*")
    logger.info("Posts cache invalidated")


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def publish_scheduled_posts()->None:
    from apps.blog.models import Post
    import redis as sync_redis 

    now =timezone.now()
    due = Post.objects.filter(status=Post.Status.SCHEDULED,
                              publish_at__lte=now)
    

    from django.conf import settings
    r = sync_redis.from_url(settings.REDIS_URL)
    for post in due:
        post.status = Post.Status.PUBLISHED
        post.save(update_fields=["status"])
        r.publish("post_published", json.dumps({
            "post_id": post.id, "title": post.title, "slug": post.slug,
            "author": {"id": post.author.id, "email": post.author.email},
            "published_at": now.isoformat(),
        }))
    logger.info(f"Published {due.count()} scheduled posts")

    



@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_daily_stats() -> None:
    from apps.blog.models import Post, Comment
    from apps.users.models import CustomUser
    since = timezone.now() - timezone.timedelta(hours=24)
    posts    = Post.objects.filter(created_at__gte=since).count()
    comments = Comment.objects.filter(created_at__gte=since).count()
    users    = CustomUser.objects.filter(date_joined__gte=since).count()
    logger.info(f"Daily stats — posts: {posts}, comments: {comments}, users: {users}")