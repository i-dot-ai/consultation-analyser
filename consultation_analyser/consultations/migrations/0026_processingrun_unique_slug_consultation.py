# Generated by Django 5.0.7 on 2024-07-22 21:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0025_generate_slugs_for_existing"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="processingrun",
            constraint=models.UniqueConstraint(
                fields=("slug", "consultation"), name="unique_slug_consultation"
            ),
        ),
    ]
