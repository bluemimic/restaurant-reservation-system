from django import forms
from django.utils.translation import gettext_lazy as _

from src.offers.models import Offer
from src.reservations.models import Reservation


class OfferChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Offer) -> str:
        return _("%(food)s, %(restaurant)s") % {
            "food": obj.name,
            "restaurant": obj.restaurant.name,
        }


class ReservationCreateForm(forms.ModelForm):
    offer = OfferChoiceField(
        queryset=Offer.objects.select_related("restaurant")
        .filter(portions_available__gt=0)
        .order_by("restaurant__name", "name"),
        required=False,
        empty_label=_("Select food"),
        label=_("Food"),
    )

    class Meta:
        model = Reservation
        fields = ["client_name", "table_number", "offer", "portions_reserved", "restaurant"]
        labels = {
            "client_name": _("Client name"),
            "table_number": _("Counter number"),
            "portions_reserved": _("Portions reserved"),
            "restaurant": _("Restaurant"),
        }

    def clean(self):
        cleaned_data = super().clean()
        offer = cleaned_data.get("offer")

        if offer is not None:
            cleaned_data["restaurant"] = offer.restaurant

        return cleaned_data


class ReservationEditForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["client_name", "table_number", "portions_reserved"]
        labels = {
            "client_name": _("Client name"),
            "table_number": _("Counter number"),
            "portions_reserved": _("Portions reserved"),
        }


class CartAddForm(forms.Form):
    portions = forms.IntegerField(
        min_value=1,
        initial=1,
        label=_("Portions"),
    )


class CartCheckoutForm(forms.Form):
    client_name = forms.CharField(
        max_length=255,
        label=_("Client name"),
    )
    client_phone = forms.CharField(
        max_length=20,
        label=_("Phone number"),
    )
