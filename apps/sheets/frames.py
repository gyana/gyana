from apps.base.frames import TurboFrameDetailView, TurboFrameUpdateView
from apps.projects.mixins import ProjectMixin
from apps.sheets.forms import SheetUpdateForm
from django.urls import reverse
from django.utils import timezone

from .bigquery import get_last_modified_from_drive_file
from .models import Sheet
from .tasks import run_update_sheets_sync


class SheetProgress(TurboFrameDetailView):
    template_name = "sheets/progress.html"
    model = Sheet
    fields = []
    turbo_frame_dom_id = "sheets:progress"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data[
            "external_table_sync_task_id"
        ] = self.object.external_table_sync_task_id

        return context_data


class SheetStatus(TurboFrameUpdateView):
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

    def form_valid(self, form):
        result = run_update_sheets_sync.delay(self.object.id)
        self.object.external_table_sync_task_id = result.task_id
        self.object.external_table_sync_started = timezone.now()
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_sheets:detail",
            args=(
                self.object.project.id,
                self.object.id,
            ),
        )


class SheetUpdate(TurboFrameUpdateView):
    template_name = "sheets/update.html"
    model = Sheet
    form_class = SheetUpdateForm
    turbo_frame_dom_id = "sheets:update"

    def form_valid(self, form):
        result = run_update_sheets_sync.delay(self.object.id)
        self.object.external_table_sync_task_id = result.task_id
        self.object.external_table_sync_started = timezone.now()
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail",
            args=(
                self.object.integration.project.id,
                self.object.integration.id,
            ),
        )
