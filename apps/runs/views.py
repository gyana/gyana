from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView

from apps.base.turbo import TurboCreateView, TurboUpdateView

from .forms import RunForm
from .models import Run
from .tables import RunTable


class RunList(SingleTableView):
    template_name = "runs/list.html"
    model = Run
    table_class = RunTable
    paginate_by = 20


class RunCreate(TurboCreateView):
    template_name = "runs/create.html"
    model = Run
    form_class = RunForm
    success_url = reverse_lazy('runs:list')


class RunDetail(DetailView):
    template_name = "runs/detail.html"
    model = Run


class RunUpdate(TurboUpdateView):
    template_name = "runs/update.html"
    model = Run
    form_class = RunForm
    success_url = reverse_lazy('runs:list')


class RunDelete(DeleteView):
    template_name = "runs/delete.html"
    model = Run
    success_url = reverse_lazy('runs:list')
