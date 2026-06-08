from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="client_phone",
            field=models.CharField(
                blank=True,
                help_text="Contact phone number for the client",
                max_length=20,
                null=True,
                verbose_name="Phone Number",
            ),
        ),
        migrations.AlterField(
            model_name="reservation",
            name="table_number",
            field=models.IntegerField(
                blank=True,
                help_text="Food court counter or stand number for pickup.",
                null=True,
                verbose_name="Counter Number",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="reservation",
            name="check_table_number_positive",
        ),
        migrations.AddConstraint(
            model_name="reservation",
            constraint=models.CheckConstraint(
                condition=models.Q(table_number__isnull=True) | models.Q(table_number__gt=0),
                name="check_table_number_positive",
            ),
        ),
    ]
