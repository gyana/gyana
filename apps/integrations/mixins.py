from django.shortcuts import redirect
from django.utils.functional import cached_property

from apps.projects.mixins import ProjectMixin

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


class TableInstanceMixin:
    @cached_property
    def table_instance(self):
        table_id = self.request.GET.get("table_id")
        return self.object.get_table_by_pk_safe(table_id)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["table_instance"] = self.table_instance
        return context_data
