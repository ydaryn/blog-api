"""
seed_data — populate the database with realistic test data.
Creates users, categories, tags, posts (draft + published), and comments.
Safe to run multiple times — skips objects that already exist.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.blogs.models import Category, Tag, Post, Comment, PostStatus

User = get_user_model()

CATEGORIES = [
    {"name_en": "Technology", "name_ru": "Технологии", "name_kk": "Технология"},
    {"name_en": "Science",    "name_ru": "Наука",       "name_kk": "Ғылым"},
    {"name_en": "Travel",     "name_ru": "Путешествия", "name_kk": "Саяхат"},
    {"name_en": "Food",       "name_ru": "Еда",         "name_kk": "Тамақ"},
]

TAGS = [
    ("python", "python"), ("django", "django"), ("api", "api"),
    ("tutorial", "tutorial"), ("news", "news"), ("ai", "ai"),
]

USERS = [
    {"email": "alice@example.com",  "first_name": "Alice",  "last_name": "Smith",    "preferred_language": "en", "timezone": "UTC"},
    {"email": "boris@example.com",  "first_name": "Boris",  "last_name": "Ivanov",   "preferred_language": "ru", "timezone": "Europe/Moscow"},
    {"email": "aizat@example.com",  "first_name": "Aizat",  "last_name": "Bekova",   "preferred_language": "kk", "timezone": "Asia/Almaty"},
    {"email": "carol@example.com",  "first_name": "Carol",  "last_name": "Jones",    "preferred_language": "en", "timezone": "America/New_York"},
    {"email": "damir@example.com",  "first_name": "Damir",  "last_name": "Seitkali", "preferred_language": "kk", "timezone": "Asia/Almaty"},
]

POSTS = [
    {
        "title": "Getting Started with Django REST Framework",
        "slug": "getting-started-drf",
        "body": "Django REST Framework (DRF) is a powerful toolkit for building Web APIs. In this post we walk through the basics of setting up DRF, creating serializers, views, and routers. By the end you will have a fully working CRUD API.",
        "status": PostStatus.PUBLISHED,
        "category": "Technology",
        "tags": ["django", "python", "api"],
        "author_email": "alice@example.com",
    },
    {
        "title": "Understanding asyncio in Python",
        "slug": "asyncio-python",
        "body": "Python's asyncio library allows you to write concurrent code using the async/await syntax. This post explains the event loop, coroutines, and how to run multiple I/O tasks concurrently with asyncio.gather.",
        "status": PostStatus.PUBLISHED,
        "category": "Technology",
        "tags": ["python", "tutorial"],
        "author_email": "alice@example.com",
    },
    {
        "title": "AI in 2026: What to Expect",
        "slug": "ai-2026",
        "body": "Artificial Intelligence continues to evolve rapidly. Large language models are now embedded in everyday tools, autonomous agents handle complex workflows, and multimodal models blend vision, audio, and text seamlessly.",
        "status": PostStatus.PUBLISHED,
        "category": "Science",
        "tags": ["ai", "news"],
        "author_email": "boris@example.com",
    },
    {
        "title": "Travelling Through Kazakhstan",
        "slug": "travelling-kazakhstan",
        "body": "Kazakhstan is a vast and beautiful country with stunning steppes, dramatic mountains, and vibrant cities like Almaty and Astana. This post covers the highlights of a two-week road trip across the country.",
        "status": PostStatus.PUBLISHED,
        "category": "Travel",
        "tags": ["news"],
        "author_email": "aizat@example.com",
    },
    {
        "title": "Draft: Upcoming Food Guide",
        "slug": "draft-food-guide",
        "body": "This post is still being written. It will cover the best traditional Kazakh dishes, including beshbarmak, kuyrdak, and baursak.",
        "status": PostStatus.DRAFT,
        "category": "Food",
        "tags": [],
        "author_email": "aizat@example.com",
    },
    {
        "title": "Building a REST API with Django",
        "slug": "building-rest-api-django",
        "body": "REST APIs are the backbone of modern web applications. In this tutorial we build a complete blog API from scratch using Django and DRF, including authentication with JWT, pagination, filtering, and Redis caching.",
        "status": PostStatus.PUBLISHED,
        "category": "Technology",
        "tags": ["django", "api", "tutorial"],
        "author_email": "carol@example.com",
    },
    {
        "title": "Introduction to Redis",
        "slug": "intro-redis",
        "body": "Redis is an in-memory data store used for caching, pub/sub messaging, and session storage. We look at how to integrate Redis with Django for caching API responses and for real-time comment notifications.",
        "status": PostStatus.PUBLISHED,
        "category": "Technology",
        "tags": ["python", "tutorial"],
        "author_email": "damir@example.com",
    },
    {
        "title": "Draft: Science of Sleep",
        "slug": "draft-science-sleep",
        "body": "Work in progress — exploring the latest research on sleep cycles, circadian rhythms, and their effect on productivity.",
        "status": PostStatus.DRAFT,
        "category": "Science",
        "tags": [],
        "author_email": "carol@example.com",
    },
]

COMMENTS = [
    ("getting-started-drf",  "boris@example.com",  "Great introduction! Very helpful for beginners."),
    ("getting-started-drf",  "aizat@example.com",  "I followed this guide and had my API running in under an hour."),
    ("asyncio-python",       "damir@example.com",  "asyncio.gather is a game changer for I/O-bound tasks."),
    ("asyncio-python",       "carol@example.com",  "Would love to see a follow-up post on asyncio with Django."),
    ("ai-2026",              "alice@example.com",  "Fascinating read. The pace of AI development is incredible."),
    ("ai-2026",              "aizat@example.com",  "I wonder how this will affect jobs in the next five years."),
    ("travelling-kazakhstan","boris@example.com",  "Charyn Canyon is absolutely breathtaking!"),
    ("building-rest-api-django", "alice@example.com", "Excellent tutorial, very clear and well-structured."),
    ("building-rest-api-django", "damir@example.com", "The section on pagination saved me a lot of time."),
    ("intro-redis",          "boris@example.com",  "Redis pub/sub is perfect for real-time features."),
]


class Command(BaseCommand):
    help = "Seed the database with test data for development."

    def handle(self, *args, **options):
        self._create_users()
        self._create_categories()
        self._create_tags()
        self._create_posts()
        self._create_comments()
        self.stdout.write(self.style.SUCCESS("✓ Database seeded successfully."))

    def _create_users(self):
        for data in USERS:
            email = data["email"]
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    email=email,
                    password="password123",
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    preferred_language=data["preferred_language"],
                    timezone=data["timezone"],
                )
                self.stdout.write(f"  Created user {email}")

    def _create_categories(self):
        for data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name_en=data["name_en"],
                defaults={"name_ru": data["name_ru"], "name_kk": data["name_kk"]},
            )
            if created:
                self.stdout.write(f"  Created category {cat.name_en}")

    def _create_tags(self):
        for name, slug in TAGS:
            tag, created = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
            if created:
                self.stdout.write(f"  Created tag {name}")

    def _create_posts(self):
        for data in POSTS:
            if Post.objects.filter(slug=data["slug"]).exists():
                continue
            author = User.objects.get(email=data["author_email"])
            category = Category.objects.get(name_en=data["category"])
            post = Post.objects.create(
                title=data["title"],
                slug=data["slug"],
                body=data["body"],
                status=data["status"],
                author=author,
                category=category,
            )
            for tag_slug in data["tags"]:
                try:
                    post.tags.add(Tag.objects.get(slug=tag_slug))
                except Tag.DoesNotExist:
                    pass
            self.stdout.write(f"  Created post '{post.title}'")

    def _create_comments(self):
        for post_slug, author_email, body in COMMENTS:
            try:
                post = Post.objects.get(slug=post_slug)
                author = User.objects.get(email=author_email)
            except (Post.DoesNotExist, User.DoesNotExist):
                continue
            if not Comment.objects.filter(post=post, author=author, body=body).exists():
                Comment.objects.create(post=post, author=author, body=body)
                self.stdout.write(f"  Created comment by {author_email} on '{post_slug}'")
