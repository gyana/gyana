from apps.base.models import BaseModel
from apps.projects.models import Project
from django.db import models
from django.urls import reverse


class Template(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    templated_projects = models.ManyToManyField(
        Project, related_name="templates", through="TemplateInstance"
    )

    def __str__(self):
        return self.project.name

    def get_absolute_url(self):
        return reverse("templates:detail", args=(self.pk,))


class TemplateInstance(BaseModel):

    # show that a project used a template that no longer exists
    template = models.ForeignKey(Template, null=True, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
