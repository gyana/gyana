from datetime import time, timedelta

from django.db import models
from django_celery_beat.models import PeriodicTask

from apps.base.models import BaseModel
from apps.projects.models import Project


class Schedule(BaseModel):
    # default midnight
    daily_schedule_time = models.TimeField(default=time())
    periodic_task = models.OneToOneField(
        PeriodicTask, null=True, on_delete=models.SET_NULL
    )
    project = models.OneToOneField(Project, on_delete=models.CASCADE)

    @property
    def next_daily_sync_in_utc(self):
        from .schedule import get_next_daily_sync_in_utc_from_schedule

        return get_next_daily_sync_in_utc_from_schedule(self)

    @property
    def truncated_daily_schedule_time(self):
        # The sync time for connectors in 15/30/45 offset timezones is earlier, due to limitations of Fivetran
        return self.next_daily_sync_in_utc.astimezone(self.team.timezone).time()

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

    def update_schedule(self):
        from .schedule import update_periodic_task_from_project

        update_periodic_task_from_project(self)

    def update_daily_sync_time(self):
        from apps.connectors.models import Connector

        connectors = Connector.objects.filter(integration__project=self.project).all()
        for connector in connectors:
            connector.sync_updates_from_fivetran()

        self.update_schedule()
