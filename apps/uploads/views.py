import analytics
from apps.base.segment_analytics import (
    INTEGRATION_CREATED_EVENT,
    NEW_INTEGRATION_START_EVENT,
)
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from apps.uploads.models import Upload
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic.detail import DetailView
from turbo_response.views import TurboCreateView

from .forms import UploadCreateForm
from .tasks import run_initial_upload_sync


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
            "project_integrations_uploads:detail",
            args=(self.project.id, self.object.id),
        )


class UploadDetail(ProjectMixin, DetailView):
    template_name = "uploads/detail.html"
    model = Upload

    def get(self, request, *args, **kwargs):
        upload = self.get_object()
        if not upload.is_syncing:
            return HttpResponseRedirect(
                reverse(
                    "project_integrations:detail",
                    args=(self.project.id, upload.integration.id),
                )
            )
        return super().get(request, *args, **kwargs)
