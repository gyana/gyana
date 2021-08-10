import analytics
from apps.base.segment_analytics import INTEGRATION_CREATED_EVENT
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse
from django.utils import timezone
from django.views.generic import DetailView
from apps.base.turbo import TurboCreateView

from .forms import SheetCreateForm
from .models import Sheet
from .tasks import run_initial_sheets_sync


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

        result = run_initial_sheets_sync.delay(self.object.id)
        self.object.sync_task_id = result.task_id
        self.object.sync_started = timezone.now()
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

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT
        return context_data

    def get(self, request, *args, **kwargs):
        sheet = self.get_object()
        if not sheet.is_syncing:
            return HttpResponseRedirect(
                reverse(
                    "project_integrations:detail",
                    args=(self.project.id, sheet.integration.id),
                )
            )
        return super().get(request, *args, **kwargs)
