import uuid

from django.conf import settings
from django.db import models
from django.db.models.fields import Field
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    id: Field = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
        help_text=_("The unique identifier for the record."),
    )

    created_at: Field = models.DateTimeField(
        db_index=True,
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("The date and time when the record was created."),
    )
    updated_at: Field = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("The date and time when the record was last updated."),
    )

    created_by: Field = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        verbose_name=_("Created By"),
        help_text=_("The user who created the record."),
    )

    updated_by: Field = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        verbose_name=_("Updated By"),
        help_text=_("The user who last updated the record."),
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    is_deleted: Field = models.BooleanField(
        null=False,
        blank=False,
        default=False,
        db_index=True,
        verbose_name=_("Is Deleted"),
        help_text=_("Indicates whether the record has been soft deleted."),
    )

    class Meta:
        abstract = True
