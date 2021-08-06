import uuid

import analytics
from apps.base.segment_analytics import NEW_INTEGRATION_START_EVENT
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django.http.response import HttpResponseBadRequest
from django.urls import reverse
from turbo_response.stream import TurboStream
from turbo_response.views import TurboCreateView

from .forms import CSVCreateForm


class IntegrationUpload(ProjectMixin, TurboCreateView):
    template_name = "uploads/upload.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind.CSV

        return context_data

    def get_initial(self):
        initial = super().get_initial()
        initial["kind"] = Integration.Kind.CSV
        initial["project"] = self.project

        return initial

    def get_form_class(self):
        analytics.track(
            self.request.user.id,
            NEW_INTEGRATION_START_EVENT,
            {"type": Integration.Kind.CSV},
        )

        return CSVCreateForm

    def form_valid(self, form):
        instance_session_key = uuid.uuid4().hex

        if not form.is_valid():
            return HttpResponseBadRequest()

        self.request.session[instance_session_key] = {
            **form.cleaned_data,
            "project": form.cleaned_data["project"].id,
        }

        return (
            TurboStream("create-container")
            .append.template(
                "uploads/file_setup/_create_flow.html",
                {
                    "instance_session_key": instance_session_key,
                    "file_input_id": "id_file",
                    "stage": "upload",
                },
            )
            .response(self.request)
        )

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail", args=(self.project.id, self.object.id)
        )
