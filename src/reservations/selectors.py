from uuid import UUID

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
import django_filters

from src.common.utils import get_object_or_none
from src.core.exceptions import NotFoundError

from .models import Reservation


class ReservationFilterSet(FilterSet):
    status = django_filters.ChoiceFilter(
        field_name="reservation_status", choices=Reservation.ReservationStatus.choices
    )

    class Meta:
        model = Reservation
        fields = {
            "restaurant": ["exact"],
        }


class ReservationSelectors:
    NOT_FOUND_ERROR = _("Reservation not found.")

    def get_reservation_by_id(self, id: UUID) -> Reservation:
        reservation = get_object_or_none(Reservation, id=id)

        if reservation is None:
            raise NotFoundError(self.NOT_FOUND_ERROR)

        return reservation

    def get_reservations(self, filters: dict | None = None) -> QuerySet[Reservation]:
        """
        Returns all reservations. Pass {"restaurant": <uuid>} in filters
        to get reservations for a specific restaurant.
        """
        filters = filters or {}

        qs = Reservation.objects.select_related("restaurant", "offer").all()

        return ReservationFilterSet(data=filters, queryset=qs).qs.order_by("-created_at")
