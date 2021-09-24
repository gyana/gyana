from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from apps.base.turbo import TurboCreateView, TurboUpdateView

from .forms import CNameForm
from .models import CName
from .tables import CNameTable


class CNameList(SingleTableView):
    template_name = "cnames/list.html"
    model = CName
    table_class = CNameTable
    paginate_by = 20


class CNameCreate(TurboCreateView):
    template_name = "cnames/create.html"
    model = CName
    form_class = CNameForm
    success_url = reverse_lazy('cnames:list')


class CNameDetail(DetailView):
    template_name = "cnames/detail.html"
    model = CName


class CNameUpdate(TurboUpdateView):
    template_name = "cnames/update.html"
    model = CName
    form_class = CNameForm
    success_url = reverse_lazy('cnames:list')


class CNameDelete(DeleteView):
    template_name = "cnames/delete.html"
    model = CName
    success_url = reverse_lazy('cnames:list')
