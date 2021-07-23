from apps.projects.models import Project
from apps.utils.models import BaseModel
from django.db import models
from django.urls import reverse
from model_clone import CloneMixin


class Workflow(CloneMixin, BaseModel):
    name = models.CharField(max_length=255, default="Untitled")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    last_run = models.DateTimeField(null=True)
    data_updated = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_workflows:detail", args=(self.project.id, self.id))

    @property
    def failed(self):
        return any(node.error is not None for node in self.nodes.all())

    @property
    def out_of_date(self):
        return self.last_run < self.data_updated if self.last_run else True
