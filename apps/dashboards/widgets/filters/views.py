from apps.dashboards.mixins import DashboardMixin
from apps.dashboards.widgets.mixins import WidgetMixin
from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from lib.bigquery import get_columns
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import get_filter_form
from .models import Filter


class FilterList(DashboardMixin, WidgetMixin, ListView):
    template_name = "filters/list.html"
    model = Filter
    paginate_by = 20


class FilterCreate(DashboardMixin, WidgetMixin, TurboCreateView):
    template_name = "filters/create.html"
    model = Filter

    @property
    def column(self):
        return self.request.GET.get("column")

    @property
    def column_type(self):
        schema = get_columns(self.widget.dataset)
        return [c.field_type for c in schema if c.name == self.column][0]

    def get_form_class(self):
        if self.column is not None:
            return get_filter_form(self.column_type)
        return get_filter_form()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = [(f.name, f.name) for f in get_columns(self.widget.dataset)]
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["widget"] = self.widget
        for key in self.request.GET:
            initial[key] = self.request.GET[key]
        return initial

    def form_valid(self, form: forms.Form) -> HttpResponse:
        form.instance.type = self.column_type
        return super().form_valid(form)

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

    @property
    def column_type(self):
        schema = get_columns(self.widget.dataset)
        return [c.field_type for c in schema if c.name == self.object.column][0]

    def get_form_class(self):
        return get_filter_form(self.object.type)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = [(f.name, f.name) for f in get_columns(self.widget.dataset)]
        return kwargs

    def form_valid(self, form: forms.Form) -> HttpResponse:
        form.instance.type = self.column_type
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:widgets:filters:update",
            args=(self.dashboard.id, self.widget.id, self.object.id),
        )


class FilterDelete(DashboardMixin, WidgetMixin, DeleteView):
    template_name = "filters/delete.html"
    model = Filter

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:widgets:filters:list", args=(self.dashboard.id, self.widget.id)
        )
