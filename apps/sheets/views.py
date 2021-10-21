import analytics
from apps.base.analytics import INTEGRATION_CREATED_EVENT, NEW_INTEGRATION_START_EVENT
from apps.base.turbo import TurboCreateView
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.urls import reverse
from django.urls.base import reverse

from .forms import SheetCreateForm
from .models import Sheet


class SheetCreate(ProjectMixin, TurboCreateView):
    template_name = "sheets/create.html"
    model = Sheet
    form_class = SheetCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["created_by"] = self.request.user
        kwargs["url"] = self.request.GET.get("url")

        return kwargs

    def get(self, request, *args, **kwargs):
        analytics.track(
            self.request.user.id,
            NEW_INTEGRATION_START_EVENT,
            {"type": Integration.Kind.SHEET},
        )
        return super().get(request, *args, **kwargs)

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
                "id": self.object.integration.id,
                "type": Integration.Kind.SHEET,
                "name": self.object.integration.name,
            },
        )

        return r

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:configure",
            args=(self.project.id, self.object.integration.id),
        )
