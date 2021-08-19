import analytics
from apps.base.segment_analytics import INTEGRATION_CREATED_EVENT
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from apps.sheets.forms import SheetUpdateForm
from django.conf import settings
from django.urls import reverse
from django.urls.base import reverse

from .forms import SheetCreateForm
from .models import Sheet
from .tasks import run_sheet_sync


class SheetCreate(ProjectMixin, TurboCreateView):
    template_name = "sheets/create.html"
    model = Sheet
    form_class = SheetCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["created_by"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT
        return context_data

    def form_valid(self, form):

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

        return r

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:configure",
            args=(self.project.id, self.object.integration.id),
        )


class SheetUpdate(ProjectMixin, TurboUpdateView):
    template_name = "sheets/update.html"
    model = Sheet
    form_class = SheetUpdateForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration"] = self.object.integration
        return context_data

    def form_valid(self, form):
        run_sheet_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_sheets:load",
            args=(self.project.id, self.object.id),
        )


class SheetLoad(ProjectMixin, TurboUpdateView):
    template_name = "sheets/load.html"
    model = Sheet
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.sync_task_id
        context_data["integration"] = self.object.integration
        return context_data

    def form_valid(self, form):
        run_sheet_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_sheets:load",
            args=(self.project.id, self.object.id),
        )
