# Generated by Django 3.2.5 on 2021-08-24 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0012_remove_team_row_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='override_row_limit',
            field=models.BigIntegerField(null=True),
        ),
    ]
