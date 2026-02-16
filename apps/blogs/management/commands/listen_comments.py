import redis
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Listen for new comments and print them to the console"

    def handle(self, *args, **options):
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        pubsub = r.pubsub()
        pubsub.subscribe("new_comments")
        self.stdout.write(self.style.SUCCESS("Listening for new comments..."))
        for message in pubsub.listen():
            if message["type"] == "message":
                comment_data = message["data"].decode("utf-8")
                self.stdout.write(self.style.SUCCESS(f"New comment: {comment_data}"))