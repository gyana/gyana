import analytics
from django.urls import reverse

from apps.base.analytics import INTEGRATION_CREATED_EVENT, NEW_INTEGRATION_START_EVENT
from apps.base.views import CreateView
from apps.integrations.models import Integration
from apps.integrations.tasks import run_integration
from apps.projects.mixins import ProjectMixin
from apps.uploads.models import Upload

from .forms import UploadCreateForm
from .models import Upload


class UploadCreate(ProjectMixin, CreateView):
    template_name = "uploads/create.html"
    model = Upload
    form_class = UploadCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["created_by"] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        analytics.track(
            self.request.user.id,
            NEW_INTEGRATION_START_EVENT,
            {"type": Integration.Kind.UPLOAD},
        )
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        r = super().form_valid(form)

        analytics.track(
            self.request.user.id,
            INTEGRATION_CREATED_EVENT,
            {
                "id": self.object.integration.id,
                "type": Integration.Kind.UPLOAD,
                "name": self.object.integration.name,
            },
        )

        run_integration(
            Integration.Kind.UPLOAD,
            self.object,
            self.request.user,
        )

        return r

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:load",
            args=(self.project.id, self.object.integration.id),
        )
