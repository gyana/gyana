# Generated by Django 3.2 on 2021-05-10 23:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("filters", "0001_initial"),
        ("widgets", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="filter",
            name="widget",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="widgets.widget"
            ),
        ),
    ]
