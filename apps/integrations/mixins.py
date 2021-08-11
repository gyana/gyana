from apps.projects.mixins import ProjectMixin
from django.http.response import HttpResponseRedirect
from django.urls import reverse


class ReadyMixin(ProjectMixin):
    def get(self, request, *args, **kwargs):
        integration = self.get_object()
        if not integration.ready:
            return HttpResponseRedirect(
                reverse(
                    "project_integrations:setup",
                    args=(self.project.id, integration.id),
                )
            )
        return super().get(request, *args, **kwargs)
