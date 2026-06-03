from django import forms
from django.utils.translation import gettext_lazy as _

from src.offers.models import Offer


class OfferCreateForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["name", "description", "price", "portions_available", "image", "category"]
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "price": _("Price"),
            "portions_available": _("Portions available"),
            "image": _("Image"),
            "category": _("Category"),
        }


class OfferEditForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ["name", "description", "price", "portions_available", "image", "category"]
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "price": _("Price"),
            "portions_available": _("Portions available"),
            "image": _("Image"),
            "category": _("Category"),
        }
