from decouple import config
SECRET_KEY=config("BLOG_SECRET_KEY")
DEBUG=config("BLOG_DEBUG", default=False, cast=bool)
REDIS_URL = config("BLOG_REDIS_URL")
