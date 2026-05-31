from uuid import UUID

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
import django_filters

from src.common.utils import get_object_or_none
from src.core.exceptions import NotFoundError

from .models import Offer


class OfferFilterSet(FilterSet):
    category = django_filters.ChoiceFilter(choices=Offer.Category.choices)
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Offer
        fields = {
            "name": ["icontains"],
            "restaurant": ["exact"],
        }


class OfferSelectors:
    NOT_FOUND_ERROR = _("Offer not found.")

    def get_offer_by_id(self, id: UUID) -> Offer:
        offer = get_object_or_none(Offer, id=id)

        if offer is None:
            raise NotFoundError(self.NOT_FOUND_ERROR)

        return offer

    def get_offers(self, filters: dict | None = None) -> QuerySet[Offer]:
        """
        Returns all offers. Pass {"restaurant": <uuid>} in filters to get
        offers for a specific restaurant.
        """
        filters = filters or {}

        qs = Offer.objects.select_related("restaurant").all()

        return OfferFilterSet(data=filters, queryset=qs).qs.order_by("-created_at")
