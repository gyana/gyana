# Generated by Django 3.2.7 on 2021-12-06 21:14

import json

from django.db import migrations
from django_celery_beat.models import CrontabSchedule, PeriodicTask


def add_periodic_task(schedule):

    schedule = CrontabSchedule.objects.create(
        minute=0,
        hour=schedule.daily_schedule_time.hour,
        timezone=schedule.project.team.timezone,
    )

    periodic_task = PeriodicTask.objects.create(
        crontab=schedule,
        # name is unique, prevents duplicate schedules for a single project
        name=f"schedules_schedule.pk={schedule.id}",
        task="apps.schedules.periodic.run_schedule",
        args=json.dumps([schedule.id]),
        enabled=False,
    )

    schedule.periodic_task = periodic_task
    schedule.save()


def forwards_func(apps, schema_editor):

    Project = apps.get_model("projects", "Project")
    Schedule = apps.get_model("schedules", "Schedule")

    for project in Project.objects.all():
        schedule = Schedule.objects.create(
            project=project, daily_schedule_time=project.daily_schedule_time
        )
        add_periodic_task(schedule)


def backwards_func(apps, schema_editor):

    Project = apps.get_model("projects", "Project")

    for project in Project.objects.all():
        project.daily_schedule_time = project.schedule.daily_schedule_time
        project.save()


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0013_project_periodic_task"),
        ("schedules", "0001_initial"),
    ]

    operations = [migrations.RunPython(code=forwards_func, reverse_code=backwards_func)]
