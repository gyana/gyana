from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView

from .forms import TemplateForm
from .models import Template
from .tables import TemplateTable


class TemplateList(TeamMixin, SingleTableView):
    template_name = "templates/list.html"
    model = Template
    table_class = TemplateTable
    paginate_by = 20


class TemplateCreate(TurboCreateView):
    template_name = "templates/create.html"
    model = Template
    form_class = TemplateForm
    success_url = reverse_lazy("templates:list")


class TemplateDetail(DetailView):
    template_name = "templates/detail.html"
    model = Template


class TemplateUpdate(TurboUpdateView):
    template_name = "templates/update.html"
    model = Template
    form_class = TemplateForm
    success_url = reverse_lazy("templates:list")


class TemplateDelete(DeleteView):
    template_name = "templates/delete.html"
    model = Template
    success_url = reverse_lazy("templates:list")
