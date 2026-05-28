from src.common.utils import get_object_or_none
from src.users.models import Restaurant
from src.core.exceptions import NotFoundError

from django.db.models import QuerySet
from django_filters import FilterSet
from uuid import UUID

class RestaurantFilterSet(FilterSet):
    class Meta:
        model = Restaurant
        fields = {
            "name": ["icontains"],
        }

class RestaurantSelectors:
    def __init__(self, performed_by: Restaurant):
        self.performed_by = performed_by

    NOT_FOUND_ERROR = _("Restaurant not found.")

    def get_restaurant_by_id(self, id: UUID) -> Restaurant:
        restaurant = get_object_or_none(Restaurant, id=id)

        if restaurant is None:
            raise NotFoundError(self.NOT_FOUND_ERROR)

        return restaurant

    def get_restaurants(self, filters: dict | None = None) -> QuerySet[Restaurant]:
        filters = filters or {}

        qs = Restaurant.objects.all()

        return RestaurantFilterSet(data=filters, queryset=qs).qs.order_by("-created_at")