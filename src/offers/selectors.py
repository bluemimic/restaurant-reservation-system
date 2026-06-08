from uuid import UUID

import django_filters
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet

from src.common.utils import get_object_or_none
from src.core.exceptions import NotFoundError

from .models import Offer


class OfferFilterSet(FilterSet):
    category = django_filters.ChoiceFilter(choices=Offer.Category.choices)
    price = django_filters.RangeFilter(field_name="price", label=_("Price"))

    class Meta:
        model = Offer
        fields = {
            "name": ["icontains"],
            "restaurant": ["exact"],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        restaurant_field = self.form.fields["restaurant"]
        restaurant_field.label_from_instance = lambda obj: obj.name
        restaurant_field.queryset = restaurant_field.queryset.filter(is_superuser=False).order_by("name")

        price_field = self.form.fields["price"]
        for subwidget, placeholder in zip(price_field.widget.widgets, ("min", "max"), strict=True):
            subwidget.attrs.setdefault("class", "form-control form-control-sm")
            subwidget.attrs.setdefault("placeholder", placeholder)
            subwidget.attrs.setdefault("min", "0")
            subwidget.attrs.setdefault("step", "0.01")


class OfferSelectors:
    NOT_FOUND_ERROR = _("Offer not found.")

    def get_offer_by_id(self, id: UUID) -> Offer:
        offer = get_object_or_none(Offer, id=id)

        if offer is None:
            raise NotFoundError(self.NOT_FOUND_ERROR)

        return offer

    def get_offers(self, filters: dict | None = None) -> QuerySet[Offer]:
        filters = filters or {}
        qs = Offer.objects.select_related("restaurant").all()
        return OfferFilterSet(data=filters, queryset=qs).qs.order_by("-created_at")
