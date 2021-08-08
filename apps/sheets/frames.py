from apps.base.frames import TurboFrameUpdateView
from django.urls import reverse

from .models import Sheet


class IntegrationSync(TurboFrameUpdateView):
    template_name = "sheets/sync.html"
    model = Sheet
    fields = []
    turbo_frame_dom_id = "integrations:sync"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data[
            "external_table_sync_task_id"
        ] = self.object.external_table_sync_task_id

        return context_data

    def form_valid(self, form):
        # todo: fix this - move to separate page?
        # self.object.sheet.start_sheets_sync()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("sheets:sync", args=(self.object.id,))
