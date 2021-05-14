from urllib.parse import parse_qs, urlparse

from apps.widgets.models import Widget
from django import forms
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import get_filter_form
from .models import Filter


class WidgetMixin:
    @property
    def widget(self):
        params = parse_qs(urlparse(self.request.META["HTTP_REFERER"]).query)
        return Widget.objects.get(pk=params["widget_id"][0])


class FilterList(WidgetMixin, ListView):
    template_name = "filters/list.html"
    model = Filter
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Filter.objects.filter(widget=self.widget).all()


class FilterCreate(WidgetMixin, TurboCreateView):
    template_name = "filters/create.html"
    model = Filter

    @property
    def column(self):
        return self.request.GET.get("column")

    @property
    def column_type(self):
        schema = self.widget.table.schema
        return schema[self.column]

    def get_form_class(self):
        if self.column is not None:
            return get_filter_form(self.column_type)
        return get_filter_form()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = [(col, col) for col in self.widget.table.schema]
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
        return reverse("filters:list")


class FilterDetail(DetailView):
    template_name = "filters/detail.html"
    model = Filter


class FilterUpdate(WidgetMixin, TurboUpdateView):
    template_name = "filters/update.html"
    model = Filter

    @property
    def column_type(self):
        schema = self.widget.table.schema
        return schema[self.object.column]

    def get_form_class(self):
        return get_filter_form(self.object.type)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = [(col, col) for col in self.widget.table.schema]
        return kwargs

    def form_valid(self, form: forms.Form) -> HttpResponse:
        form.instance.type = self.column_type
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("filters:update", args=(self.object.id,))


class FilterDelete(DeleteView):
    template_name = "filters/delete.html"
    model = Filter

    def get_success_url(self) -> str:
        return reverse("filters:list")
