# Generated by Django 3.2.5 on 2021-08-10 16:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sheets", "0008_auto_20210809_2355"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sheet",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="sheet",
            name="project",
        ),
        migrations.RemoveField(
            model_name="sheet",
            name="sheet_name",
        ),
    ]
