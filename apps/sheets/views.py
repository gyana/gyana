from apps.projects.mixins import ProjectMixin
from django import forms
from django.http import HttpResponse
from django.urls.base import reverse
from django.views.generic import DetailView
from turbo_response.views import TurboCreateView

from .forms import SheetForm
from .models import Sheet


class SheetCreate(ProjectMixin, TurboCreateView):
    template_name = "sheets/create.html"
    model = Sheet
    form_class = SheetForm

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project
        return initial

    def form_valid(self, form: forms.Form) -> HttpResponse:
        form.instance.start_sheets_sync()
        return super().form_valid(form)

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
