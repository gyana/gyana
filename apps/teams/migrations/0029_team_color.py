# Generated by Django 3.2.11 on 2022-02-16 12:48
import random

import apps.teams.utils
from django.db import migrations, models

# These were taken from fusioncharts.theme.fusion.js as the default values
# for a chart palette.
def getRandomColor():

    return random.choice([
        "#ccfbf1",
        "#cffafe",
        "#d1fae5",
        "#dcfce7",
        "#e0e7ff",
        "#e0f2fe",
        "#ecfccb",
        "#ede9fe",
        "#f3e8ff",
        "#fae8ff",
        "#fce7f3",
        "#fee2e2",
        "#fef3c7",
        "#fef9c3",
        "#ffe4e6",
        "#ffedd5",
    ])


def generate_uuid(apps, schema_editor):
    Team = apps.get_model('teams', 'Team')
    for team in Team.objects.all().iterator():
        team.color = getRandomColor()

        team.save()


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0028_team_override_credit_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='color',
            field=models.CharField(default=getRandomColor, max_length=7),
        ),
        migrations.RunPython(
            generate_uuid,
            migrations.RunPython.noop
        ),
    ]
