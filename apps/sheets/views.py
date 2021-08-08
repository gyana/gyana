import analytics
from apps.base.segment_analytics import INTEGRATION_CREATED_EVENT
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django import forms
from django.http import HttpResponse
from django.urls.base import reverse
from django.views.generic import DetailView
from turbo_response.views import TurboCreateView

from .forms import SheetForm
from .models import Sheet
from .tasks import run_sheets_sync


class SheetCreate(ProjectMixin, TurboCreateView):
    template_name = "sheets/create.html"
    model = Sheet
    form_class = SheetForm

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project
        return initial

    def form_valid(self, form: forms.Form) -> HttpResponse:

        form.instance.created_by = self.request.user

        r = super().form_valid(form)

        analytics.track(
            self.request.user.id,
            INTEGRATION_CREATED_EVENT,
            {
                # not the same as integration.id
                "id": form.instance.id,
                "type": Integration.Kind.SHEET,
                # not available for a sheet
                # "name": form.instance.name,
            },
        )

        result = run_sheets_sync.delay(self.object.id)
        self.object.external_table_sync_task_id = result.task_id
        self.object.save()

        return r

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_sheets:detail",
            args=(
                self.project.id,
                self.object.id,
            ),
        )


class SheetDetail(ProjectMixin, DetailView):
    template_name = "sheets/detail.html"
    model = Sheet
