from django.db import models
from django.utils.translation import gettext_lazy as _

from src.common.models import BaseModel


class Offer(BaseModel):
    class Category(models.TextChoices):
        ASIAN = "asian", _("Asian")
        ITALIAN = "italian", _("Italian")
        MEXICAN = "mexican", _("Mexican")
        AMERICAN = "american", _("American")
        VEGETARIAN = "vegetarian", _("Vegetarian")
        VEGAN = "vegan", _("Vegan")
        PIZZA = "pizza", _("Pizza")
        BURGER = "burger", _("Burger")
        SALAD = "salad", _("Salad")
        DESSERT = "dessert", _("Dessert")
        DRINK = "drink", _("Drink")
        KEBAB = "kebab", _("Kebab")
        JAPANESE = "japanese", _("Japanese")
        INDIAN = "indian", _("Indian")
        HALAL = "halal", _("Halal")
        OTHER = "other", _("Other")

    name: models.CharField = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Offer Name"),
        help_text=_("Name of the offer"),
    )

    description: models.TextField = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Offer Description"),
        help_text=_("Detailed description of the offer"),
    )

    price: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False,
        blank=False,
        verbose_name=_("Offer Price"),
        help_text=_("Price of the offer"),
    )

    portions_available: models.IntegerField = models.IntegerField(
        null=False,
        blank=False,
        verbose_name=_("Portions Available"),
        help_text=_("Number of portions available for this offer"),
    )

    image: models.ImageField = models.ImageField(
        upload_to="offer_images/",
        null=True,
        blank=True,
        verbose_name=_("Offer Image"),
        help_text=_("Image representing the offer"),
    )

    category: models.CharField = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
        verbose_name=_("Offer Category"),
        help_text=_("Category of the offer"),
    )

    restaurant: models.ForeignKey = models.ForeignKey(
        "users.Restaurant",
        on_delete=models.CASCADE,
        verbose_name=_("Restaurant"),
        help_text=_("Restaurant offering the deal"),
    )


    class Meta:
        verbose_name = _("Offer")
        verbose_name_plural = _("Offers")

        constraints: list[models.CheckConstraint] = [
            models.CheckConstraint(condition=models.Q(price__gte=0), name="check_price_non_negative"),
            models.CheckConstraint(condition=models.Q(portions_available__gte=0), name="check_portions_non_negative"),
        ]
