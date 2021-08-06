from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import SheetForm
from .models import Sheet
from .tables import SheetTable


class SheetList(SingleTableView):
    template_name = "sheets/list.html"
    model = Sheet
    table_class = SheetTable
    paginate_by = 20


class SheetCreate(TurboCreateView):
    template_name = "sheets/create.html"
    model = Sheet
    form_class = SheetForm
    success_url = reverse_lazy('sheets:list')


class SheetDetail(DetailView):
    template_name = "sheets/detail.html"
    model = Sheet


class SheetUpdate(TurboUpdateView):
    template_name = "sheets/update.html"
    model = Sheet
    form_class = SheetForm
    success_url = reverse_lazy('sheets:list')


class SheetDelete(DeleteView):
    template_name = "sheets/delete.html"
    model = Sheet
    success_url = reverse_lazy('sheets:list')
