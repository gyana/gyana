import json
from datetime import time, timedelta

import pytz
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from apps.base.models import BaseModel
from apps.projects.models import Project


class Schedule(BaseModel):
    # default midnight
    daily_schedule_time = models.TimeField(default=time())
    periodic_task = models.OneToOneField(
        PeriodicTask, null=True, on_delete=models.SET_NULL
    )
    project = models.OneToOneField(Project, on_delete=models.CASCADE)

    @staticmethod
    def create_with_periodic_task(project: Project):

        schedule = Schedule.objects.create(project=project)

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

        return schedule

    @property
    def next_daily_sync_in_utc(self):
        # Calculate the next sync time in UTC. It will change over time thanks
        # to daily savings. Start with the local time of the user, calculate
        # the next sync time they expect to see, and convert it back to UTC.

        today_local = timezone.now().astimezone(self.project.team.timezone)
        next_sync_time_local = today_local.replace(
            hour=self.daily_schedule_time.hour, minute=0, second=0, microsecond=0
        )
        if next_sync_time_local < today_local:
            next_sync_time_local += timedelta(days=1)

        next_sync_time_utc = next_sync_time_local.astimezone(pytz.UTC)

        # for timezones with 15/30/45 minute offset, we prefer to round down
        # to guarantee it has started
        return next_sync_time_utc.replace(minute=0)

    @property
    def truncated_daily_schedule_time(self):
        # The sync time for connectors in 15/30/45 offset timezones is earlier, due to limitations of Fivetran
        return self.next_daily_sync_in_utc.astimezone(self.project.team.timezone).time()

    @property
    def next_sync_time_utc_string(self):
        # For daily sync, Fivetran requires a HH:MM formatted string in UTC
        return self.next_daily_sync_in_utc.strftime("%H:%M")

    @property
    def latest_schedule(self):
        # the most recent schedule time in the past
        return self.next_daily_sync_in_utc - timedelta(days=1)

    @property
    def needs_schedule(self):
        from apps.sheets.models import Sheet
        from apps.workflows.models import Workflow

        # A project only requires an active shedule if there are scheduled
        # entities like sheets, workflows, apis etc.

        return (
            Sheet.objects.is_scheduled_in_project(self.project).exists()
            or Workflow.objects.is_scheduled_in_project(self.project).exists()
        )

    @property
    def latest_schedule_is_complete(self):
        from apps.sheets.models import Sheet
        from apps.workflows.models import Workflow

        # check for schedule entities which have neither succeeded or failed today

        expr = Q(failed_at__gt=self.latest_schedule) | Q(
            succeeded_at__gt=self.latest_schedule
        )

        return (
            not Sheet.objects.is_scheduled_in_project(self.project)
            .exclude(expr)
            .exists()
            and not Workflow.objects.is_scheduled_in_project(self.project)
            .exclude(expr)
            .exists()
        )

    def update_schedule(self):
        self.periodic_task.crontab.update(
            hour=self.daily_schedule_time.hour,
            timezone=self.project.team.timezone,
        )
        self.periodic_task.update(enabled=self.needs_schedule)

    def update_daily_sync_time(self):
        from apps.connectors.models import Connector

        connectors = Connector.objects.filter(integration__project=self.project).all()
        for connector in connectors:
            connector.sync_updates_from_fivetran()

        self.update_schedule()
