
#third-party  imports
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser


User = get_user_model()


@database_sync_to_async 
def get_user_from_token(token_str):

    try:
        token = AccessToken(token_str)
        return User.objects.get(id=token["user_id"])
        

    except Exception:
        return AnonymousUser()



class JWTAuthMiddleware:
    """Reads ?token=<access_token> from 
    the WebSocket URL and authenticates the user."""

    def __init__(self,app):
        self.app =app

    

    async def __call__(self, scope, recieve,send):
        qs = parse_qs(scope["query_string"].decode())
        token_str = qs.get("token",[None])[0]
        scope["user"] = await get_user_from_token(token_str) if token_str else AnonymousUser()
        return await self.app(scope,recieve,send)







