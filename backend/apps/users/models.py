#python-modules
from typing import Any
from django.contrib.auth.models import ( 
    AbstractBaseUser, 
    PermissionsMixin, 
    BaseUserManager,
)
from django.db.models import (
    CharField,
    EmailField, 
    BooleanField,
    DateTimeField,
    ImageField,
)
from django.conf import settings
from django.utils.translation import gettext_lazy as _
# project imports
from apps.abstract.models import AbstractTimeStampModel

from apps.users.manager import CustomUserManager



FIRST_NAME_MAX_LENGTH = 50
LAST_NAME_MAX_LENGTH = 50


class CustomUser(
    AbstractBaseUser,
    AbstractTimeStampModel,
    PermissionsMixin
):
    email=EmailField(
        unique=True,
        verbose_name=_("emal"),
    )
    first_name=CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
        verbose_name=_("first name"),
    
    )
    last_name=CharField(
        max_length=LAST_NAME_MAX_LENGTH,
        verbose_name=_("last name"),
    )
    is_active=BooleanField(
        default=True,
        verbose_name=_("active"),
    )
    is_staff=BooleanField(
        default=False,
        verbose_name =_("is staff"),
    )
    data_jonded=DateTimeField(
        auto_now_add=True,
    )
    avatar=ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name =_("avatar"),
    )
    preferred_language = CharField(
        max_length=10,
        choices=settings.LANGUAGES,
        default="en",
        verbose_name=_("preferred language"),
    )
    timezone=CharField(
        max_length=100,
        default="UTC",
        verbose_name=_("timezone"),
        
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]
    
    objects = CustomUserManager()

    class Meta:
        verbose_name=_("user")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"