# Generated by Django 4.0.4 on 2022-06-02 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0023_connector_has_import_triggered'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connector',
            name='has_import_triggered',
            field=models.BooleanField(default=False),
        ),
    ]
