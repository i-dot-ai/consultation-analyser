# Generated by Django 5.0.6 on 2024-07-04 22:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0022_alter_question_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="topicmodelmetadata",
            name="scatter_plot_data",
            field=models.JSONField(default=dict),
        ),
    ]