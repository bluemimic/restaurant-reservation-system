from django.db import models
from django.db.models import CheckConstraint
from django.utils.translation import gettext_lazy as _

from src.common.models import BaseModel


class Reservation(BaseModel):
    class ReservationStatus(models.TextChoices):
        CREATED = "created", _("Created")
        ACCEPTED = "accepted", _("Accepted")
        DENIED = "denied", _("Denied")
        PREPARED = "prepared", _("Prepared")
        DELIVERED = "delivered", _("Delivered")
        CANCELED = "canceled", _("Canceled")

    client_name: models.CharField = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Client Name"),
        help_text=_("Name of the client making the reservation"),
    )

    client_phone: models.CharField = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Contact phone number for the client"),
    )

    table_number: models.IntegerField = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Counter Number"),
        help_text=_("Food court counter or stand number for pickup."),
    )

    offer: models.ForeignKey = models.ForeignKey(
        "offers.Offer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reservations",
        verbose_name=_("Offer"),
        help_text=_("The offer associated with this reservation, if any"),
    )

    restaurant: models.ForeignKey = models.ForeignKey(
        "users.Restaurant",
        on_delete=models.CASCADE,
        verbose_name=_("Restaurant"),
        help_text=_("Restaurant offering the deal"),
    )

    portions_reserved: models.IntegerField = models.IntegerField(
        null=False,
        blank=False,
        verbose_name=_("Portions Reserved"),
        help_text=_("Number of portions reserved for this reservation"),
    )

    reservation_status: models.CharField = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.CREATED,
        verbose_name=_("Reservation Status"),
        help_text=_("Current status of the reservation"),
    )

    class Meta:
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")

        constraints: list[CheckConstraint] = [
            CheckConstraint(
                condition=models.Q(table_number__isnull=True) | models.Q(table_number__gt=0),
                name="check_table_number_positive",
            ),
            CheckConstraint(condition=models.Q(portions_reserved__gt=0), name="check_portions_reserved_positive"),
        ]
