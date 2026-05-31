# mypy: disable-error-code="assignment"


from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager as BUM
from django.db import models
from django.db.models.fields import Field
from django.utils.translation import gettext_lazy as _

from src.common.models import BaseModel, SoftDeleteModel
from src.common.validators import CustomEmailValidator


class BaseUserManager(BUM):
    def create_user(
        self,
        email: str,
        name: str,
        is_active: bool = True,
        password: str | None = None,
    ):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email.lower()),
            name=name,
            is_active=is_active,
        )

        if password is not None:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.full_clean()
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, name: str, password: str | None = None):
        user = self.create_user(
            email=email,
            name=name,
            is_active=True,
            password=password,
        )

        user.is_superuser = True
        user.save(using=self._db)

        return user


class Restaurant(SoftDeleteModel, BaseModel, AbstractBaseUser, PermissionsMixin):
    name: Field = models.CharField(
        max_length=255, null=False, blank=False, verbose_name=_("Name"), help_text=_("The name of the restaurant.")
    )

    email: Field = models.EmailField(
        validators=[
            CustomEmailValidator(),
        ],
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        verbose_name=_("Email address"),
        help_text=_("The email address of the user."),
        error_messages={
            "unique": _("A user with this email already exists."),
        },
    )

    password: Field = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Password"),
        help_text=_("The hashed password of the user."),
    )

    is_active: Field = models.BooleanField(
        default=True,
        verbose_name=_("Is active?"),
        help_text=_("Designates whether this user should be treated as active."),
        null=False,
        blank=False,
    )

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = BaseUserManager()

    def __str__(self):
        return f"{self.name} ({self.email})"

    def get_full_name(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
