from apps.teams.models import Team
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    description = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

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

    def num_rows(self):
        from apps.tables.models import Table

        return Table.objects.filter(integration__project=self).aggregate(
            models.Sum("num_rows")
        )["num_rows__sum"]
