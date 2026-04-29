# Python modules
import random

# Django modules
from django.core.management.base import BaseCommand
from django.utils.text import slugify

# Project modules
from apps.blog.models import Post, Category, Tag, Comment
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Seed database with test data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        # Users
        users = []
        for i in range(1, 4):
            email = f"user{i}@blog.com"
            if not CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.create_user(
                    email=email,
                    first_name=f"User{i}",
                    last_name="Test",
                    password="testpass123",
                )
                users.append(user)
                self.stdout.write(f"  Created user: {email}")
            else:
                users.append(CustomUser.objects.get(email=email))

        # Categories
        categories_data = [
            ("technology", "Technology", "Технологии", "Технология"),
            ("science", "Science", "Наука", "Ғылым"),
            ("sports", "Sports", "Спорт", "Спорт"),
        ]
        categories = []
        for slug, en, ru, kk in categories_data:
            if not Category.objects.filter(slug=slug).exists():
                cat = Category.objects.language("en").create(slug=slug, name=en)
                cat.set_current_language("ru")
                cat.name = ru
                cat.save()
                cat.set_current_language("kk")
                cat.name = kk
                cat.save()
                self.stdout.write(f"  Created category: {en}")
            categories.append(Category.objects.get(slug=slug))

        # Tags
        tags_data = ["python", "django", "api", "rest", "async"]
        tags = []
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(
                slug=tag_name,
                defaults={"name": tag_name},
            )
            tags.append(tag)
            if created:
                self.stdout.write(f"  Created tag: {tag_name}")

        # Posts
        posts_data = [
            ("Django REST Framework Guide", "published"),
            ("Async Python with asyncio", "published"),
            ("Redis Pub/Sub Tutorial", "published"),
            ("Draft Post Example", "draft"),
            ("Another Published Post", "published"),
            ("Python Tips and Tricks", "published"),
        ]
        for i, (title, status) in enumerate(posts_data):
            slug = slugify(title)
            if not Post.objects.filter(slug=slug).exists():
                post = Post.objects.create(
                    author=users[i % len(users)],
                    title=title,
                    body=f"This is the content of {title}. " * 10,
                    status=status,
                    category=random.choice(categories),
                )
                post.tags.set(random.sample(tags, k=2))
                self.stdout.write(f"  Created post: {title}")

        # Comments
        posts = Post.objects.filter(status="published")
        for post in posts:
            for j in range(3):
                if not Comment.objects.filter(post=post, body=f"Comment {j} on {post.title}").exists():
                    Comment.objects.create(
                        post=post,
                        author=random.choice(users),
                        body=f"Comment {j} on {post.title}",
                    )
            self.stdout.write(f"  Created comments for: {post.title}")

        self.stdout.write(self.style.SUCCESS("✓ Seeding complete!"))
