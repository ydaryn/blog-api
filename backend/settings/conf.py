#Third party modules

from decouple import config
from os import environ

ENV_ID_POSSIBLE_OPTIONS = ["local", "prod"]

BLOG_ENV_ID = config("BLOG_ENV_ID", cast=str)

SECRET_KEY = 'django-insecure-(^_^gfp3**yddhcs%6q!gm@%3#6mp3nwmxr(15df$ypky$ckgv'

REDIS_HOST = config("BLOG_REDIS_HOST", default="localhost")
REDIS_PORT = config("BLOG_REDIS_PORT", default=6379, cast=int)
REDIS_DB   = config("BLOG_REDIS_DB",   default=0,    cast=int)

REDIS_CELERY_DB = config("REDIS_CELERY_DB", default=1, cast=int)


BLOG_CELERY_BROKER_URL = environ.get("BLOG_CELERY_BROKER_URL", "redis://localhost:6379/1")