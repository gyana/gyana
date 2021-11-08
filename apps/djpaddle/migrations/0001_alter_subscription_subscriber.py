# Generated by Django 3.2.7 on 2021-11-08 22:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0021_team_subscription"),
        ("djpaddle", "0004_auto_20210119_0436"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="subscriber",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subscriptions",
                to="teams.team",
            ),
        ),
    ]
