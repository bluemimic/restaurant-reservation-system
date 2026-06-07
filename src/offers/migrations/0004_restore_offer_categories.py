from django.db import migrations, models

ORIGINAL_CATEGORY_CHOICES = [
    ("asian", "Asian"),
    ("italian", "Italian"),
    ("mexican", "Mexican"),
    ("american", "American"),
    ("vegetarian", "Vegetarian"),
    ("vegan", "Vegan"),
    ("pizza", "Pizza"),
    ("burger", "Burger"),
    ("salad", "Salad"),
    ("dessert", "Dessert"),
    ("drink", "Drink"),
    ("kebab", "Kebab"),
    ("japanese", "Japanese"),
    ("indian", "Indian"),
    ("halal", "Halal"),
    ("other", "Other"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("offers", "0003_reduce_offer_categories"),
    ]

    operations = [
        migrations.AlterField(
            model_name="offer",
            name="category",
            field=models.CharField(
                choices=ORIGINAL_CATEGORY_CHOICES,
                default="other",
                help_text="Category of the offer",
                max_length=20,
                verbose_name="Offer Category",
            ),
        ),
    ]
