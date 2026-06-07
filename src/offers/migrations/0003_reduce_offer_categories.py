from django.db import migrations, models

CATEGORY_MAP = {
    "pizza": "pizza",
    "burger": "burger",
    "asian": "asian",
    "italian": "italian",
    "vegetarian": "vegetarian",
    "dessert": "dessert",
    "drink": "drink",
    "other": "other",
    "japanese": "asian",
    "indian": "asian",
    "kebab": "asian",
    "halal": "asian",
    "mexican": "other",
    "american": "other",
    "vegan": "vegetarian",
    "salad": "vegetarian",
}

CATEGORY_CHOICES = [
    ("pizza", "Pizza"),
    ("burger", "Burger"),
    ("asian", "Asian"),
    ("italian", "Italian"),
    ("vegetarian", "Vegetarian"),
    ("dessert", "Dessert"),
    ("drink", "Drink"),
    ("other", "Other"),
]


def map_legacy_categories(apps, schema_editor):
    Offer = apps.get_model("offers", "Offer")

    for offer in Offer.objects.all():
        new_category = CATEGORY_MAP.get(offer.category, "other")
        if offer.category != new_category:
            offer.category = new_category
            offer.save(update_fields=["category"])


class Migration(migrations.Migration):
    dependencies = [
        ("offers", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(map_legacy_categories, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="offer",
            name="category",
            field=models.CharField(
                choices=CATEGORY_CHOICES,
                default="other",
                help_text="Category of the offer",
                max_length=20,
                verbose_name="Offer Category",
            ),
        ),
    ]
