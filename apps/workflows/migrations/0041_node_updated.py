# Generated by Django 3.2 on 2021-07-13 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0040_auto_20210713_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
