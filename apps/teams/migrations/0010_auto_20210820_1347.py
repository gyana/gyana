# Generated by Django 3.2.5 on 2021-08-20 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0009_team_row_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='team',
            name='row_count',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='team',
            name='row_count_calculated',
            field=models.DateTimeField(null=True),
        ),
    ]
