from apps.projects.mixins import ProjectMixin
from django.shortcuts import redirect

from .models import Integration

STATE_TO_URL_REDIRECT = {
    Integration.State.UPDATE: "project_integrations:configure",
    Integration.State.LOAD: "project_integrations:load",
    Integration.State.ERROR: "project_integrations:load",
    Integration.State.DONE: "project_integrations:done",
}


class ReadyMixin(ProjectMixin):
    def get(self, request, *args, **kwargs):
        integration = self.get_object()
        if not integration.ready:
            url_name = STATE_TO_URL_REDIRECT[integration.state]
            return redirect(url_name, self.project.id, integration.id)
        return super().get(request, *args, **kwargs)
