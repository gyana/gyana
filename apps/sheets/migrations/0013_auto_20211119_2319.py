# Generated by Django 3.2.7 on 2021-11-19 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sheets", "0012_auto_20211105_0139"),
    ]

    operations = [
        migrations.AddField(
            model_name="sheet",
            name="failed_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="sheet",
            name="is_scheduled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="sheet",
            name="next_daily_sync",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="sheet",
            name="succeeded_at",
            field=models.DateTimeField(null=True),
        ),
    ]
