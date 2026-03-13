"""
listen_comments — async Redis pub/sub listener.

Why async?
  The synchronous redis.pubsub().listen() blocks the OS thread while waiting
  for the next message.  With asyncio + redis.asyncio we yield control back
  to the event loop between messages, so the process stays responsive and can
  be combined with other coroutines (health-checks, metrics, etc.) without
  needing threads.  A purely synchronous version would be simpler but would
  block any co-routine scheduled alongside it.
"""
import asyncio
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger("apps.blogs.listen_comments")


class Command(BaseCommand):
    help = "Listen for new comment events on the Redis 'new_comments' channel (async)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting async comment listener…"))
        asyncio.run(self._listen())

    async def _listen(self):
        # redis.asyncio is bundled with the redis package ≥ 4.2
        import redis.asyncio as aioredis

        r = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
        )
        async with r.pubsub() as pubsub:
            await pubsub.subscribe("new_comments")
            self.stdout.write(self.style.SUCCESS("Subscribed to 'new_comments'. Waiting…"))
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    post_slug = data.get("post_slug", "?")
                    author_id = data.get("author_id", "?")
                    body = data.get("body", "")
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[new comment] post={post_slug}  author={author_id}  "
                            f"body={body[:80]}"
                        )
                    )
                except Exception as exc:
                    logger.warning("Malformed comment event: %s — %s", message["data"], exc)
