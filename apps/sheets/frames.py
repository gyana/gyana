from django.views.generic import DetailView

from .models import Sheet


class SheetStatus(DetailView):
    template_name = "sheets/status.html"
    model = Sheet
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        self.object.sync_updates_from_drive()
        return context_data
