from datetime import datetime, time, timedelta

import pytz
from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from model_clone.mixins.clone import CloneMixin

from apps.base.models import BaseModel
from apps.cnames.models import CName
from apps.teams.models import Team


class Project(DirtyFieldsMixin, CloneMixin, BaseModel):
    class Access(models.TextChoices):
        EVERYONE = ("everyone", "Everyone in your team can access")
        INVITE_ONLY = ("invite", "Only invited team members can access")

    name = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    # False if created from a template
    ready = models.BooleanField(default=True)
    access = models.CharField(
        max_length=8, choices=Access.choices, default=Access.EVERYONE
    )
    description = models.TextField(blank=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="invite_only_projects",
        through="ProjectMembership",
    )
    cname = models.ForeignKey(CName, on_delete=models.SET_NULL, null=True, blank=True)
    # default midnight
    daily_schedule_time = models.TimeField(default=time())

    _clone_m2o_or_o2m_fields = ["integration_set", "workflow_set", "dashboard_set"]

    def __str__(self):
        return self.name

    @property
    def next_daily_sync(self):
        # Calculate the next sync time in UTC. It will change over time thanks
        # to daily savings. Start with the local time of the user, calculate
        # the next sync time they expect to see, and convert it back to UTC.

        today_local = timezone.now().astimezone(self.team.timezone)
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
        return self.next_daily_sync.astimezone(self.team.timezone).time()

    @property
    def next_sync_time_utc_string(self):
        return self.next_daily_sync.strftime("%H:%M")

    @property
    def integration_count(self):
        return self.integration_set.exclude(
            connector__fivetran_authorized=False
        ).count()

    @property
    def workflow_count(self):
        return self.workflow_set.count()

    @property
    def dashboard_count(self):
        return self.dashboard_set.count()

    @property
    def is_template(self):
        return hasattr(self, "template")

    @property
    def has_pending_templates(self):
        return self.templateinstance_set.filter(completed=False).count() != 0

    @cached_property
    def num_rows(self):
        from apps.tables.models import Table

        return (
            Table.available.filter(integration__project=self).aggregate(
                models.Sum("num_rows")
            )["num_rows__sum"]
            or 0
        )

    @cached_property
    def integrations_for_review(self):
        return self.integration_set.review().count()

    def update_daily_sync_time(self):
        from apps.connectors.models import Connector
        from apps.sheets.models import Sheet

        connectors = Connector.objects.filter(integration__project=self).all()
        for connector in connectors:
            connector.sync_updates_from_fivetran()

        sheets = Sheet.objects.filter(integration__project=self).all()
        for sheet in sheets:
            sheet.update_next_daily_sync()

    def get_absolute_url(self):
        return reverse("projects:detail", args=(self.id,))


class ProjectMembership(BaseModel):
    """
    A user's project membership
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
