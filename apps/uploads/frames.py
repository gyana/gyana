from apps.base.frames import TurboFrameDetailView

from .models import Upload


class UploadProgress(TurboFrameDetailView):
    template_name = "uploads/progress.html"
    model = Upload
    turbo_frame_dom_id = "uploads:progress"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.sync_task_id

        return context_data
