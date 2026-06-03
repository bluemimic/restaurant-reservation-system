from django import forms
from django.utils.translation import gettext_lazy as _

from src.reservations.models import Reservation


class ReservationCreateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["client_name", "table_number", "offer", "portions_reserved", "restaurant"]
        labels = {
            "client_name": _("Client name"),
            "table_number": _("Table number"),
            "offer": _("Offer"),
            "portions_reserved": _("Portions reserved"),
            "restaurant": _("Restaurant"),
        }


class ReservationEditForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["client_name", "table_number", "portions_reserved"]
        labels = {
            "client_name": _("Client name"),
            "table_number": _("Table number"),
            "portions_reserved": _("Portions reserved"),
        }
