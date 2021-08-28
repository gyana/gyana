from apps.base.frames import TurboFrameDetailView

from .bigquery import get_last_modified_from_drive_file
from .models import Sheet


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
