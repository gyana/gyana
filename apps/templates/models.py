from apps.base.models import BaseModel
from apps.projects.models import Project
from apps.templates.duplicate import template_integration_is_ready_in_project
from django.db import models


class Template(BaseModel):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    templated_projects = models.ManyToManyField(
        Project, related_name="templates", through="TemplateInstance"
    )

    @property
    def name(self):
        return self.project.name

    @property
    def description(self):
        return self.project.description

    def __str__(self):
        return self.project.name


class TemplateInstance(BaseModel):

    # show that a project used a template that no longer exists
    template = models.ForeignKey(Template, null=True, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    @property
    def is_ready(self):
        return all(
            template_integration_is_ready_in_project(t, self.project)
            for t in self.template.project.integration_set.all()
        )
