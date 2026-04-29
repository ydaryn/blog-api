import json 
import logging 
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
#project imports 
from apps.blog.models import Post
logger = logging.getLogger(__name__)


class CommentConsumer(AsyncWebsocketConsumer):


    async def connect(self):

        if isinstance(self.scope["user"],AnonymousUser):
            await self.close(code=4001)
            return 
        
        slug = self.scope["url_route"]["kwargs"]["slug"]
        exists = await self._post_exists(slug)
        if not exists:
            await self.close(code=4004)
            return 
        


        self.group_name = f"post_{slug}_comments"

        await self.channel_layer.group_add(self.group_name,self.channel_name)
        
        await self.accept()
        logger.info(f"WS connected: user={self.scope['user'].email}, slug={slug}")

    

    async def disconnect(self,close_code):
        if hasattr(self,"group_name"):
            await self.channel_layer.group_discard(self.group_name,self.channel_name)

    
    async def new_comment(self,event):
        await self.send(text_data=json.dumps(event["data"]))
    

    @database_sync_to_async
    def _post_exists(self,slug):
        return Post.objects.filter(slug=slug).exists()