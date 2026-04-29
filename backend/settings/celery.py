#python imports 
import os 
from celery import Celery 
from celery.schedules import crontab 
from settings.conf import BLOG_ENV_ID, ENV_ID_POSSIBLE_OPTIONS

assert BLOG_ENV_ID in ENV_ID_POSSIBLE_OPTIONS, (
    f"Set correct BLOG_ENV_ID env var. Possible options: {ENV_ID_POSSIBLE_OPTIONS}"
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{BLOG_ENV_ID}")
app = Celery("blog")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "publish-scheduled-posts": {
        "task": "apps.blog.tasks.publish_scheduled_posts",
        "schedule": crontab(minute="*/1"),
    },
    # Daily at 06:00 — clear old notifications
    "clear-expired-notifications": {
        "task": "apps.notifications.tasks.clear_expired_notifications",
        "schedule": crontab(hour=6, minute=0),
    },
    # Daily at 12:00 — log daily stats
    "generate-daily-stats": {
        "task": "apps.blog.tasks.generate_daily_stats",
        "schedule": crontab(hour=12, minute=0),
    },
}
