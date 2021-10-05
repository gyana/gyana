from functools import cached_property

from apps.base.models import BaseModel
from apps.cnames.models import CName
from apps.teams.models import Team
from django.conf import settings
from django.db import models
from django.urls import reverse
from model_clone.mixins.clone import CloneMixin


class Project(CloneMixin, BaseModel):
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
    cname = models.ForeignKey(CName, on_delete=models.SET_NULL, null=True)

    _clone_m2o_or_o2m_fields = ["integration_set", "workflow_set", "dashboard_set"]

    def __str__(self):
        return self.name

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
