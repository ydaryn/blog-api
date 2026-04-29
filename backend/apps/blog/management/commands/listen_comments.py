# Python modules
import asyncio
import json
import logging

# Django modules
from django.core.management.base import BaseCommand
from django.conf import settings

# Third-party modules
from channels.layers import get_channel_layer
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Subscribe to Redis comments channel using async Redis client"
    

    def handle(self, *args, **options):
        """
        Why async: Redis pub/sub is I/O bound — we're just waiting for messages.
        Sync version would block the thread while waiting.
        Async version uses asyncio event loop — no thread blocking.
        """
        slug = options.get("slug", "test")
        self.stdout.write(self.style.SUCCESS("Starting async channel layer listener..."))
        asyncio.run(self.listen(slug))

    async def listen(self, slug="test"):
        """
        Use the channel layer instead of raw Redis pub/sub.
        Receives the same messages that WebSocket clients get.
        """
        channel_layer = get_channel_layer()
        channel_name = "debug_listener"
        group_name = f"post_{slug}_comments"

        await channel_layer.group_add(group_name, channel_name)
        self.stdout.write(self.style.SUCCESS(f"Listening on group: {group_name}"))

        try:
            while True:
                message = await channel_layer.receive(channel_name)
                data = message.get("data", {})
                self.stdout.write(self.style.SUCCESS("=" * 60))
                self.stdout.write(f"  comment_id: {data.get('comment_id')}")
                self.stdout.write(f"  author:     {data.get('author')}")
                self.stdout.write(f"  body:       {data.get('body')}")
                self.stdout.write(f"  created_at: {data.get('created_at')}")
                self.stdout.write(self.style.SUCCESS("=" * 60))
        except asyncio.CancelledError:
            pass
        finally:
            await channel_layer.group_discard(group_name, channel_name)
            

    


       