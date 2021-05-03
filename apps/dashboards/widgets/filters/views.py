from apps.dashboards.mixins import DashboardMixin
from apps.dashboards.widgets.mixins import WidgetMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import FilterForm
from .models import Filter


class FilterList(DashboardMixin, WidgetMixin, ListView):
    template_name = "filters/list.html"
    model = Filter
    paginate_by = 20


class FilterCreate(DashboardMixin, WidgetMixin, TurboCreateView):
    template_name = "filters/create.html"
    model = Filter
    form_class = FilterForm
    success_url = reverse_lazy("dashboards:widgets:filters:list")


class FilterDetail(DashboardMixin, WidgetMixin, DetailView):
    template_name = "filters/detail.html"
    model = Filter


class FilterUpdate(DashboardMixin, WidgetMixin, TurboUpdateView):
    template_name = "filters/update.html"
    model = Filter
    form_class = FilterForm
    success_url = reverse_lazy("dashboards:widgets:filters:list")


class FilterDelete(DashboardMixin, WidgetMixin, DeleteView):
    template_name = "filters/delete.html"
    model = Filter
    success_url = reverse_lazy("dashboards:widgets:filters:list")
