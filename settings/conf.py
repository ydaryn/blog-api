from decouple import config

SECRET_KEY = config("BLOG_SECRET_KEY")
DEBUG = config("BLOG_DEBUG", default=False, cast=bool)
REDIS_URL = config("BLOG_REDIS_URL", default="redis://127.0.0.1:6379/0")
REDIS_HOST = config("BLOG_REDIS_HOST", default="127.0.0.1")
REDIS_PORT = config("BLOG_REDIS_PORT", default=6379, cast=int)
DEFAULT_LANGUAGE = config("BLOG_DEFAULT_LANGUAGE", default="en")
EMAIL_BACKEND_CONF = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
