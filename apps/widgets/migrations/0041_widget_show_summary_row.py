# Generated by Django 3.2.7 on 2021-12-13 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("widgets", "0040_widget_page"),
    ]

    operations = [
        migrations.AddField(
            model_name="widget",
            name="show_summary_row",
            field=models.BooleanField(
                default=False,
                help_text="Display a summary row at the bottom of your table",
            ),
        ),
    ]
