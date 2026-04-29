from django.db.models import(
    CharField,
    TextField,
    ForeignKey,
    DateTimeField,
    SlugField,
    ManyToManyField,
    TextChoices,
    CASCADE,
    SET_NULL,
)
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields


#PROJECT imports 
from apps.abstract.models import AbstractTimeStampModel
from apps.users.models import CustomUser 


CATEGORY_MAX_NAME_LENGTH = 100 
TAG_MAX_NAME_LENGTH = 50 
POST_TITLE_MAX_LENGTH = 200 


class Category(TranslatableModel,AbstractTimeStampModel):
    """
    Docstring for Category and for multilnangual fields
    """
    translations = TranslatedFields(
        name = CharField(
        max_length=CATEGORY_MAX_NAME_LENGTH,
        verbose_name =_("name"),
    )
    )
   
    slug = SlugField(
        unique=True,
    )
    class Meta:
        verbose_name = _("category")
    
    def __str__(self):
        return self.safe_translation_getter("name", any_language=True) or ""


class Tag(AbstractTimeStampModel):
    """
    Docstring for Tag
    """
    name = CharField(
        max_length=TAG_MAX_NAME_LENGTH,
        unique=True,
    )
    slug = SlugField(
        unique=True,

    )


class Post(AbstractTimeStampModel):
    """
    Docstring for Post
    """
    class Status(TextChoices):
        DRAFT = "draft"
        PUBLISHED = "published"
        SCHEDULED ="scheduled"

    
    author = ForeignKey(
        to=CustomUser, 
        on_delete= CASCADE, 
        related_name="posts",
    )

    title = CharField(
        max_length=POST_TITLE_MAX_LENGTH,
    )
    slug = SlugField(
        unique=True,
    )
    body = TextField()

    category = ForeignKey(
        to=Category,
        on_delete=SET_NULL,
        null=True,  
        blank=True, 
        related_name="posts",
    )
    tags = ManyToManyField(
        to=Tag,
        blank=True,
        related_name="posts",

    )

    status=CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    publish_at = DateTimeField(
        null =True,
        blank=True
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Comment(AbstractTimeStampModel):
    """
    Docstring for Comment
    """

    post=ForeignKey(
        to=Post,
        on_delete=CASCADE,
        related_name="comments",
    )
    author=ForeignKey(
        to=CustomUser,
        on_delete=CASCADE,
        related_name="comments",
    )
    body=TextField(
    )




    


    