from apps.teams.models import Team
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name

    def output_nodes(self):
        from apps.workflows.models import Node

        return Node.objects.filter(workflow__project=self, kind=Node.Kind.OUTPUT)
