from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(autoretry_for=(Exception,),retry_backoff=True,
             max_retries=3)
def send_welcome_email(user_id: int) ->None:
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mail
    User =get_user_model()
    user =User.objects.get(pk=user_id)

    send_mail(
        subject="Welcome to BLOG",
        message=f"Hi {user.email}, welcome!",
        from_email="noreply@blog.com",
        recipient_list=[user.email],
    )
    logger.info(f"Welcome email sent to {user.email}")
