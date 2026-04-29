from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_new_comment(comment_id: int) -> None:
    from apps.blog.models import Comment
    from apps.notifications.models import Notification
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    comment = Comment.objects.select_related("post__author", "author").get(pk=comment_id)
    post = comment.post

    if comment.author != post.author:
        Notification.objects.create(recipient=post.author, comment=comment)
        logger.info(f"Notification created for {post.author.email}")

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"post_{post.slug}_comments",
        {
            "type": "new_comment",
            "data": {
                "comment_id": comment.id,
                "author": {"id": comment.author.id, "email": comment.author.email},
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
            },
        }
    )

@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def clear_expired_notifications() -> None:
    from django.utils import timezone
    from apps.notifications.models import Notification
    cutoff = timezone.now() - timezone.timedelta(days=30)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info(f"Cleared {deleted} expired notifications")