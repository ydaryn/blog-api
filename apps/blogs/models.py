from django.db import models
from django.utils.translation import gettext_lazy as _


class PostStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PUBLISHED = "published", _("Published")


class Category(models.Model):
    # Per-language name fields
    name_en = models.CharField(_("name (English)"), max_length=100)
    name_ru = models.CharField(_("name (Russian)"), max_length=100, blank=True)
    name_kk = models.CharField(_("name (Kazakh)"), max_length=100, blank=True)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def get_name(self, lang="en"):
        return getattr(self, f"name_{lang}", None) or self.name_en

    def __str__(self):
        return self.name_en


class Tag(models.Model):
    name = models.CharField(_("name"), max_length=50, unique=True)
    slug = models.SlugField(_("slug"), max_length=50, unique=True)

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(_("title"), max_length=200)
    body = models.TextField(_("body"))
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    author = models.ForeignKey(
        "users.User", on_delete=models.CASCADE,
        related_name="posts", verbose_name=_("author")
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="posts", verbose_name=_("category")
    )
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True, verbose_name=_("tags"))
    status = models.CharField(
        _("status"), max_length=10,
        choices=PostStatus.choices, default=PostStatus.DRAFT
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("post")
        verbose_name_plural = _("posts")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name="comments", verbose_name=_("post")
    )
    author = models.ForeignKey(
        "users.User", on_delete=models.CASCADE,
        related_name="comments", verbose_name=_("author")
    )
    body = models.TextField(_("body"))
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("comment")
        verbose_name_plural = _("comments")
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.email} on {self.post.title}"
