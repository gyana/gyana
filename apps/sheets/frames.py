from apps.base.frames import TurboFrameDetailView, TurboFrameUpdateView
from apps.sheets.forms import SheetUpdateForm
from django.urls import reverse

from .bigquery import get_last_modified_from_drive_file
from .models import Sheet
from .tasks import run_sheets_sync


class SheetUpdate(TurboFrameUpdateView):
    template_name = "sheets/update.html"
    model = Sheet
    form_class = SheetUpdateForm
    turbo_frame_dom_id = "sheets:setup"

    def form_valid(self, form):
        run_sheets_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "sheets:progress",
            args=(self.object.id,),
        ) + "?refresh=true"

class SheetProgress(TurboFrameUpdateView):
    template_name = "sheets/progress.html"
    model = Sheet
    fields = []
    turbo_frame_dom_id = "sheets:setup"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.sync_task_id

        return context_data

    def form_valid(self, form):
        run_sheets_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "sheets:progress",
            args=(self.object.id,),
        )


class SheetStatus(TurboFrameDetailView):
    template_name = "sheets/status.html"
    model = Sheet
    fields = []
    turbo_frame_dom_id = "sheets:status"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["out_of_date"] = (
            get_last_modified_from_drive_file(self.object)
            > self.object.drive_file_last_modified
        )

        return context_data



