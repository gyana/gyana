from apps.projects.mixins import ProjectMixin
from django.http.response import HttpResponseRedirect
from django.urls import reverse


class ReadyMixin(ProjectMixin):
    def get(self, request, *args, **kwargs):
        integration = self.get_object()
        if not integration.ready:
            url_name = (
                "configure"
                if integration.state == "update"
                else "load"
                if integration.state in ["load", "error"]
                else "done"
            )
            return HttpResponseRedirect(
                reverse(
                    f"project_integrations:{url_name}",
                    args=(self.project.id, integration.id),
                )
            )
        return super().get(request, *args, **kwargs)
