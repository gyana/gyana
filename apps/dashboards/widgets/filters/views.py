from apps.dashboards.mixins import DashboardMixin
from apps.dashboards.widgets.mixins import WidgetMixin
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from lib.bigquery import get_columns
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = get_columns(self.widget.dataset)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["widget"] = self.widget
        return initial

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:widgets:filters:list", args=(self.dashboard.id, self.widget.id)
        )


class FilterDetail(DashboardMixin, WidgetMixin, DetailView):
    template_name = "filters/detail.html"
    model = Filter


class FilterUpdate(DashboardMixin, WidgetMixin, TurboUpdateView):
    template_name = "filters/update.html"
    model = Filter
    form_class = FilterForm

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:widgets:filters:list", args=(self.dashboard.id, self.widget.id)
        )


class FilterDelete(DashboardMixin, WidgetMixin, DeleteView):
    template_name = "filters/delete.html"
    model = Filter

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:widgets:filters:list", args=(self.dashboard.id, self.widget.id)
        )
