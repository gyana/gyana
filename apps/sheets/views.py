from apps.projects.mixins import ProjectMixin
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

    def form_invalid(self, form):
        print("HOLA")
        print(form.data, form.initial)
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        return reverse("sheets:detail", args=(self.object.id,))


class SheetDetail(DetailView):
    template_name = "sheets/detail.html"
    model = Sheet
