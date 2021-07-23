from apps.projects.models import Project
from apps.utils.models import BaseModel
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from model_clone import CloneMixin


class Dashboard(CloneMixin, BaseModel):
    name = models.CharField(max_length=255, default="Untitled")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    _clone_m2o_or_o2m_fields = ["widget_set"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_dashboards:detail", args=(self.project.id, self.id))
