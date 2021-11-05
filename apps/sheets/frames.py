from apps.base.frames import TurboFrameDetailView

from .models import Sheet
from .sheets import get_last_modified_from_drive_file


class SheetStatus(TurboFrameDetailView):
    template_name = "sheets/status.html"
    model = Sheet
    fields = []
    turbo_frame_dom_id = "sheets:status"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        self.object.sync_updates_from_drive()
        return context_data
