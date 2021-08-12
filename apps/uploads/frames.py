from apps.base.frames import TurboFrameDetailView, TurboFrameUpdateView
from apps.uploads.forms import UploadUpdateForm
from apps.uploads.tasks import run_upload_sync
from django.urls import reverse

from .models import Upload


class UploadProgress(TurboFrameDetailView):
    template_name = "uploads/progress.html"
    model = Upload
    turbo_frame_dom_id = "uploads:progress"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.sync_task_id

        return context_data


class UploadUpdate(TurboFrameUpdateView):
    template_name = "uploads/update.html"
    model = Upload
    form_class = UploadUpdateForm
    turbo_frame_dom_id = "uploads:update"

    def form_valid(self, form):
        run_upload_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:setup",
            args=(
                self.object.integration.project.id,
                self.object.integration.id,
            ),
        )
