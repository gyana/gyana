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
from django.utils import timezone

from .forms import UploadCreateForm
from .tasks import run_initial_upload_sync


class UploadCreate(ProjectMixin, TurboCreateView):
    template_name = "uploads/create.html"
    model = Upload

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

        return UploadCreateForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        r = super().form_valid(form)

        analytics.track(
            self.request.user.id,
            INTEGRATION_CREATED_EVENT,
            {
                # not the same as integration.id
                "id": form.instance.id,
                "type": Integration.Kind.UPLOAD,
                # not available for a sheet
                # "name": form.instance.name,
            },
        )

        result = run_initial_upload_sync.delay(self.object.id)
        self.object.sync_task_id = result.task_id
        self.object.sync_started = timezone.now()
        self.object.save()

        return r

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:setup",
            args=(self.project.id, self.object.integration.id),
        )
