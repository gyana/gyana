from apps.base.models import BaseModel
from apps.integrations.models import Integration
from apps.projects.models import Project
from django.db import models


class Template(BaseModel):

    """
    Templates are pointers to existing projects.
    """

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

    """
    Instances of templates that are linked to projects where the template is instantiated.
    """

    # [SET_NULL] show that a project used a template that no longer exists
    template = models.ForeignKey(Template, null=True, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    @property
    def is_ready(self):
        return (
            self.templateintegration_set.exclude(target_integration__ready=True).count()
            == 0
        )


class TemplateIntegration(BaseModel):

    """
    Integration slots that need to be instantiated, before a template is setup in a project.
    """

    template_instance = models.ForeignKey(TemplateInstance, on_delete=models.CASCADE)
    # [SET_NULL] template integrations are based on snapshot of a template project, even if
    # upstream integration is deleted we need to keep track of it here
    source_integration = models.ForeignKey(
        Integration,
        null=True,
        on_delete=models.SET_NULL,
        related_name="template_integration_source_set",
    )
    target_integration = models.ForeignKey(
        Integration,
        null=True,
        on_delete=models.SET_NULL,
        related_name="template_integration_target_set",
    )
