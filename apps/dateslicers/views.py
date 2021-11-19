from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView

from apps.base.turbo import TurboCreateView, TurboUpdateView

from .forms import DateSlicerForm
from .models import DateSlicer


class DateSlicerCreate(TurboCreateView):
    template_name = "dateslicers/create.html"
    model = DateSlicer
    form_class = DateSlicerForm
    success_url = reverse_lazy("dateslicers:list")


class DateSlicerUpdate(TurboUpdateView):
    template_name = "dateslicers/update.html"
    model = DateSlicer
    form_class = DateSlicerForm
    success_url = reverse_lazy("dateslicers:list")


class DateSlicerDelete(DeleteView):
    template_name = "dateslicers/delete.html"
    model = DateSlicer
    success_url = reverse_lazy("dateslicers:list")
