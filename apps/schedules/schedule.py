import json
from datetime import timedelta

import pytz
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from .models import Schedule


def get_next_daily_sync_in_utc_from_schedule(schedule: Schedule):
    # Calculate the next sync time in UTC. It will change over time thanks
    # to daily savings. Start with the local time of the user, calculate
    # the next sync time they expect to see, and convert it back to UTC.

    today_local = timezone.now().astimezone(schedule.project.team.timezone)
    next_sync_time_local = today_local.replace(
        hour=schedule.daily_schedule_time.hour, minute=0, second=0, microsecond=0
    )
    if next_sync_time_local < today_local:
        next_sync_time_local += timedelta(days=1)

    next_sync_time_utc = next_sync_time_local.astimezone(pytz.UTC)

    # for timezones with 15/30/45 minute offset, we prefer to round down
    # to guarantee it has started
    return next_sync_time_utc.replace(minute=0)


def update_periodic_task_from_schedule(schedule: Schedule):

    # Create, update or delete a periodic task for a project

    if schedule.needs_schedule:
        if schedule.periodic_task is None:
            schedule = CrontabSchedule.objects.create(
                minute=0,
                hour=schedule.daily_schedule_time.hour,
                timezone=schedule.project.team.timezone,
            )

            periodic_task = PeriodicTask.objects.create(
                crontab=schedule,
                # name is unique, prevents duplicate schedules for a single project
                name=f"schedules_schedule.pk={schedule.id}",
                task="apps.schedules.periodic.run_schedule_for_project",
                args=json.dumps([schedule.id]),
            )

            schedule.periodic_task = periodic_task
            schedule.save()
        else:
            crontab = schedule.periodic_task.crontab
            crontab.hour = schedule.daily_schedule_time.hour
            crontab.timezone = schedule.project.team.timezone
            crontab.save()

    elif schedule.periodic_task is not None:
        # cascading delete to periodic_task
        schedule.periodic_task.crontab.delete()
