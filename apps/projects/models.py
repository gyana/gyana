from datetime import time, timedelta

from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django_celery_beat.models import PeriodicTask

from apps.base.models import BaseModel
from apps.cnames.models import CName
from apps.teams.models import Team


class Project(DirtyFieldsMixin, BaseModel):
    class Access(models.TextChoices):
        EVERYONE = ("everyone", "Everyone in your team can access")
        INVITE_ONLY = ("invite", "Only invited team members can access")

    _clone_excluded_m2o_or_o2m_fields = ["runs", "table_set"]
    _clone_excluded_m2m_fields = ["members"]
    _clone_excluded_o2o_fields = ["periodic_task"]

    name = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

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
    periodic_task = models.OneToOneField(
        PeriodicTask, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name

    @property
    def truncated_daily_schedule_time(self):
        from .schedule import get_next_daily_sync_in_utc_from_project

        # The sync time for connectors in 15/30/45 offset timezones is earlier, due to limitations of Fivetran
        return (
            get_next_daily_sync_in_utc_from_project(self)
            .astimezone(self.team.timezone)
            .time()
        )

    @property
    def next_sync_time_utc_string(self):
        from .schedule import get_next_daily_sync_in_utc_from_project

        # For daily sync, Fivetran requires a HH:MM formatted string in UTC
        return get_next_daily_sync_in_utc_from_project(self).strftime("%H:%M")

    @property
    def latest_schedule(self):
        from .schedule import get_next_daily_sync_in_utc_from_project

        # the most recent schedule time in the past
        return get_next_daily_sync_in_utc_from_project(self) - timedelta(days=1)

    @property
    def integration_count(self):
        return self.integration_set.count()

    @property
    def workflow_count(self):
        return self.workflow_set.count()

    @property
    def dashboard_count(self):
        return self.dashboard_set.count()

    @cached_property
    def row_percentage(self):
        return round((self.num_rows / self.team.row_limit) * 100, 3)

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

    @property
    def needs_schedule(self):
        from apps.integrations.models import Integration

        # A project only requires an active shedule if there are scheduled
        # entities like sheets, workflows, apis etc.

        return (
            self.integration_set.filter(
                kind__in=Integration.KIND_RUN_IN_PROJECT,
                is_scheduled=True,
            ).exists()
            or self.workflow_set.filter(is_scheduled=True).exists()
        )

    def update_schedule(self):
        from .schedule import update_periodic_task_from_project

        update_periodic_task_from_project(self)

    def get_absolute_url(self):
        return reverse("projects:detail", args=(self.id,))

    @property
    def latest_run(self):
        return self.runs.order_by("-created").first()

    def make_clone(self, attrs=None, sub_clone=False, using=None):
        clone = super().make_clone(attrs, sub_clone, using)
        clone.update_schedule()
        return clone


class ProjectMembership(BaseModel):
    """
    A user's project membership
    """

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
