from functools import cached_property

from apps.base.models import BaseModel
from apps.teams.models import Team
from django.db import models
from django.urls import reverse
from model_clone.mixins.clone import CloneMixin


class Project(CloneMixin, BaseModel):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    # False if created from a template
    ready = models.BooleanField(default=True)

    description = models.TextField(blank=True)

    _clone_m2o_or_o2m_fields = ["integration_set", "workflow_set", "dashboard_set"]

    def __str__(self):
        return self.name

    def integration_count(self):
        from apps.integrations.models import Integration

        return Integration.objects.filter(project=self).count()

    def workflow_count(self):
        from apps.workflows.models import Workflow

        return Workflow.objects.filter(project=self).count()

    def dashboard_count(self):
        from apps.dashboards.models import Dashboard

        return Dashboard.objects.filter(project=self).count()

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
