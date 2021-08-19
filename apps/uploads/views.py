import analytics
from apps.base.segment_analytics import (
    INTEGRATION_CREATED_EVENT,
    NEW_INTEGRATION_START_EVENT,
)
from apps.base.turbo import TurboCreateView
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from apps.uploads.models import Upload
from django.urls import reverse

from .forms import UploadCreateForm
from .models import Upload


class UploadCreate(ProjectMixin, TurboCreateView):
    template_name = "uploads/create.html"
    model = Upload
    form_class = UploadCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["created_by"] = self.request.user
        return kwargs

    def get_form_class(self):
        analytics.track(
            self.request.user.id,
            NEW_INTEGRATION_START_EVENT,
            {"type": Integration.Kind.UPLOAD},
        )
        return super().get_form_class()

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        r = super().form_valid(form)

        analytics.track(
            self.request.user.id,
            INTEGRATION_CREATED_EVENT,
            {
                "id": self.object.integration.id,
                "type": Integration.Kind.UPLOAD,
                "name": self.object.integration.name,
            },
        )

        return r

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:configure",
            args=(self.project.id, self.object.integration.id),
        )
