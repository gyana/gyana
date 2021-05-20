from apps.projects.models import Project
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse


class Dashboard(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    sort_order = ArrayField(models.IntegerField(), default=list)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("projects:dashboards:detail", args=(self.project.id, self.id))
