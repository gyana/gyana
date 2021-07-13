from apps.projects.models import Project
from apps.utils.models import BaseModel
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse


class Dashboard(BaseModel):
    name = models.CharField(max_length=255, default="Untitled")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_dashboards:detail", args=(self.project.id, self.id))
