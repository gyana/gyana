# Generated by Django 3.2 on 2021-05-08 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataflows", "0016_auto_20210508_0211"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataflow",
            name="last_run",
            field=models.DateTimeField(null=True),
        ),
    ]
