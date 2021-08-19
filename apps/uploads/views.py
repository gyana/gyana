import analytics
from apps.base.segment_analytics import (
    INTEGRATION_CREATED_EVENT,
    NEW_INTEGRATION_START_EVENT,
)
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from apps.uploads.forms import UploadUpdateForm
from apps.uploads.models import Upload
from apps.uploads.tasks import run_upload_sync
from django.urls import reverse

from .forms import UploadCreateForm
from .models import Upload
from .tasks import run_upload_sync


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

        return r

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_uploads:update",
            args=(self.project.id, self.object.id),
        )


class UploadUpdate(ProjectMixin, TurboUpdateView):
    template_name = "uploads/update.html"
    model = Upload
    form_class = UploadUpdateForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration"] = self.object.integration
        return context_data

    def form_valid(self, form):
        run_upload_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_uploads:load",
            args=(self.project.id, self.object.id),
        )


class UploadLoad(ProjectMixin, TurboUpdateView):
    template_name = "uploads/load.html"
    model = Upload
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.sync_task_id
        context_data["integration"] = self.object.integration
        return context_data

    def form_valid(self, form):
        run_upload_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_uploads:load",
            args=(self.project.id, self.object.id),
        )
