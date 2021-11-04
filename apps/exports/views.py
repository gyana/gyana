from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from apps.base.turbo import TurboCreateView, TurboUpdateView

from .forms import ExportForm
from .models import Export
from .tables import ExportTable


class ExportList(SingleTableView):
    template_name = "exports/list.html"
    model = Export
    table_class = ExportTable
    paginate_by = 20


class ExportCreate(TurboCreateView):
    template_name = "exports/create.html"
    model = Export
    form_class = ExportForm
    success_url = reverse_lazy('exports:list')


class ExportDetail(DetailView):
    template_name = "exports/detail.html"
    model = Export


class ExportUpdate(TurboUpdateView):
    template_name = "exports/update.html"
    model = Export
    form_class = ExportForm
    success_url = reverse_lazy('exports:list')


class ExportDelete(DeleteView):
    template_name = "exports/delete.html"
    model = Export
    success_url = reverse_lazy('exports:list')
