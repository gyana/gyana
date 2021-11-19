from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from apps.base.turbo import TurboCreateView, TurboUpdateView

from .forms import DateSlicerForm
from .models import DateSlicer
from .tables import DateSlicerTable


class DateSlicerList(SingleTableView):
    template_name = "dateslicers/list.html"
    model = DateSlicer
    table_class = DateSlicerTable
    paginate_by = 20


class DateSlicerCreate(TurboCreateView):
    template_name = "dateslicers/create.html"
    model = DateSlicer
    form_class = DateSlicerForm
    success_url = reverse_lazy('dateslicers:list')


class DateSlicerDetail(DetailView):
    template_name = "dateslicers/detail.html"
    model = DateSlicer


class DateSlicerUpdate(TurboUpdateView):
    template_name = "dateslicers/update.html"
    model = DateSlicer
    form_class = DateSlicerForm
    success_url = reverse_lazy('dateslicers:list')


class DateSlicerDelete(DeleteView):
    template_name = "dateslicers/delete.html"
    model = DateSlicer
    success_url = reverse_lazy('dateslicers:list')
