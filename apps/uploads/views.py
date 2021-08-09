import uuid

import analytics
from apps.base.segment_analytics import NEW_INTEGRATION_START_EVENT
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from apps.uploads.models import Upload
from django.urls import reverse
from django.views.generic.detail import DetailView
from turbo_response.views import TurboCreateView

from .forms import CSVCreateForm


class UploadCreate(ProjectMixin, TurboCreateView):
    template_name = "uploads/upload.html"
    model = Upload

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project
        return initial

    def get_form_class(self):
        analytics.track(
            self.request.user.id,
            NEW_INTEGRATION_START_EVENT,
            {"type": Integration.Kind.UPLOAD},
        )

        return CSVCreateForm

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_uploads:detail", args=(self.project.id, self.object.id)
        )


class UploadDetail(ProjectMixin, DetailView):
    template_name = "uploads/detail.html"
    model = Upload
