from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
import pytz


SUPPORTED_LANGUAGES = [('en', 'English'), ('ru', 'Russian'), ('kk', 'Kazakh')]
LANGUAGE_CHOICES = [(code, name) for code, name in SUPPORTED_LANGUAGES]


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str, **extra) -> "User":
        if not email:
            raise ValueError(_("Email is required"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra) -> "User":
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(_("last name"), max_length=30)
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    avatar = models.ImageField(_("avatar"), upload_to="avatars/", null=True, blank=True)

    # hw2 fields
    preferred_language = models.CharField(
        _("preferred language"),
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default="en",
        blank=True,
    )
    timezone = models.CharField(
        _("timezone"),
        max_length=100,
        default="UTC",
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        return self.email
