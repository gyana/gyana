from django.urls import reverse

from apps.base.turbo import TurboCreateView
from apps.projects.mixins import ProjectMixin

from .forms import CustomApiCreateForm
from .models import CustomApi


class CustomApiCreate(ProjectMixin, TurboCreateView):
    template_name = "customapis/create.html"
    model = CustomApi
    form_class = CustomApiCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["created_by"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:configure",
            args=(self.project.id, self.object.integration.id),
        )
