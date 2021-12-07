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
        PeriodicTask,
        null=True,
        on_delete=models.SET_NULL,
        related_name="project_schedule",
    )
    run_task_id = models.UUIDField(null=True)
    run_started_at = models.DateTimeField(null=True)

    succeeded_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)
    cancelled_at = models.DateTimeField(null=True)

    project = models.OneToOneField(Project, on_delete=models.CASCADE)

    @property
    def is_running(self):
        if self.run_started_at is None:
            return False

        return not (
            (self.succeeded_at and self.succeeded_at > self.run_started_at)
            or (self.failed_at and self.failed_at > self.run_started_at)
            or (self.cancelled_at and self.cancelled_at > self.run_started_at)
        )

    @staticmethod
    def create_with_periodic_task(project: Project):

        schedule = Schedule.objects.create(project=project)

        crontab = CrontabSchedule.objects.create(
            minute=0,
            hour=schedule.daily_schedule_time.hour,
            timezone=schedule.project.team.timezone,
        )

        periodic_task = PeriodicTask.objects.create(
            crontab=crontab,
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
        from apps.connectors.models import Connector
        from apps.sheets.models import Sheet
        from apps.workflows.models import Workflow

        # check for schedule entities which have neither succeeded or failed today

        expr = Q(failed_at__gt=self.run_started_at) | Q(
            succeeded_at__gt=self.run_started_at
        )

        return (
            not Sheet.objects.is_scheduled_in_project(self.project)
            .exclude(expr)
            .exists()
            and not Workflow.objects.is_scheduled_in_project(self.project)
            .exclude(expr)
            .exists()
            and not Connector.objects.is_scheduled_in_project(self.project)
            .exclude(expr)
            .exists()
        )

    def update_schedule(self):
        crontab = self.periodic_task.crontab
        crontab.hour = self.daily_schedule_time.hour
        crontab.timezone = self.project.team.timezone
        crontab.save()

        self.periodic_task.enabled = self.needs_schedule
        self.save()

    def update_daily_sync_time(self):
        from apps.connectors.models import Connector

        connectors = Connector.objects.filter(integration__project=self.project).all()
        for connector in connectors:
            connector.sync_updates_from_fivetran()

        self.update_schedule()
