# Generated by Django 3.2 on 2021-05-06 04:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("connectors", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="connector",
            name="service",
            field=models.TextField(max_length=255),
        ),
    ]
