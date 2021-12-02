# Generated by Django 3.2.7 on 2021-12-02 02:31

import random

from django.db import migrations
from django_celery_beat.models import CrontabSchedule, PeriodicTask


def get_periodic_task(project):
    offset = random.randint(0, 60)
    # create a periodic task in this timezone
    # offset is to reduce load
    schedule = CrontabSchedule.objects.create(
        minute=f"{offset}-59",
        hour=project.daily_schedule_time.hour,
        timezone=project.team.timezone,
    )

    periodic_task = PeriodicTask.objects.create(
        crontab=schedule,
        name=f"Project schedule for pk={project.id}",
        task="apps.projects.tasks.run_schedule_for_project",
    )

    return periodic_task


def forwards(apps, schema_editor):
    Project = apps.get_model("projects", "Project")

    for project in Project.objects.all():
        project.periodic_task = get_periodic_task(project)
        project.save()


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0013_project_periodic_task"),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]
