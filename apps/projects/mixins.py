from django.utils.functional import cached_property

from .models import Project


class ProjectMixin:
    @cached_property
    def project(self):
        return Project.objects.get(pk=self.kwargs["project_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.project.team
        context["project"] = self.project
        return context
