import json
from datetime import timedelta

import pytz
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from .models import Project


def get_next_daily_sync_in_utc_from_project(project: Project):
    # Calculate the next sync time in UTC. It will change over time thanks
    # to daily savings. Start with the local time of the user, calculate
    # the next sync time they expect to see, and convert it back to UTC.

    today_local = timezone.now().astimezone(project.team.timezone)
    next_sync_time_local = today_local.replace(
        hour=project.daily_schedule_time.hour, minute=0, second=0, microsecond=0
    )
    if next_sync_time_local < today_local:
        next_sync_time_local += timedelta(days=1)

    next_sync_time_utc = next_sync_time_local.astimezone(pytz.UTC)

    # for timezones with 15/30/45 minute offset, we prefer to round down
    # to guarantee it has started
    return next_sync_time_utc.replace(minute=0)


def update_periodic_task_from_project(project: Project):

    # Create, update or delete a periodic task for a project

    if project.needs_schedule:
        if project.periodic_task is None:
            schedule = CrontabSchedule.objects.create(
                minute=0,
                hour=project.daily_schedule_time.hour,
                timezone=project.team.timezone,
            )

            periodic_task = PeriodicTask.objects.create(
                crontab=schedule,
                # name is unique, prevents duplicate schedules for a single project
                name=f"schedule.project.pk={project.id}",
                task="apps.projects.periodic.run_schedule_for_project",
                args=json.dumps([project.id]),
            )

            project.periodic_task = periodic_task
            project.save()
        else:
            crontab = project.periodic_task.crontab
            crontab.hour = project.daily_schedule_time.hour
            crontab.timezone = project.team.timezone
            crontab.save()

    elif project.periodic_task is not None:
        # cascading delete to periodic_task
        project.periodic_task.crontab.delete()
