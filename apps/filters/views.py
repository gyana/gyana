from functools import cached_property
from urllib.parse import parse_qs, urlparse

from apps.widgets.models import Widget
from apps.workflows.models import Node
from django import forms
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import get_filter_form
from .models import Filter

IBIS_TO_TYPE = {"Int64": "INTEGER", "String": "STRING"}


class ParentMixin:
    @cached_property
    def parent(self):
        entity, pk, *_ = self.request.META["HTTP_TURBO_FRAME"].split("-")
        if entity == "widget":
            return Widget.objects.get(pk=pk)
        if entity == "node":
            return Node.objects.get(pk=pk)
        raise Exception("No filter parent specified")

    @cached_property
    def schema(self):
        if isinstance(self.parent, Widget):
            return self.parent.table.schema
        return self.parent.schema

    @cached_property
    def parent_fk(self):
        return "widget" if isinstance(self.parent, Widget) else "node"


class FilterList(ParentMixin, ListView):
    template_name = "filters/list.html"
    model = Filter

    def get_queryset(self) -> QuerySet:
        return self.parent.filters.all()


class FilterCreate(ParentMixin, TurboCreateView):
    template_name = "filters/create.html"
    model = Filter

    @property
    def column(self):
        return self.request.GET.get("column")

    @property
    def column_type(self):
        schema = self.schema
        return schema[self.column]

    def get_form_class(self):
        if self.column is not None:
            return get_filter_form(self.parent_fk, self.column_type)
        return get_filter_form(self.parent_fk)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = [(col, col) for col in self.schema]
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial[self.parent_fk] = self.parent

        for key in self.request.GET:
            initial[key] = self.request.GET[key]
        return initial

    def form_valid(self, form: forms.Form) -> HttpResponse:
        form.instance.type = IBIS_TO_TYPE[self.column_type.name]
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("filters:list")


class FilterDetail(DetailView):
    template_name = "filters/detail.html"
    model = Filter


class FilterUpdate(ParentMixin, TurboUpdateView):
    template_name = "filters/update.html"
    model = Filter

    @property
    def column_type(self):
        schema = self.schema
        return schema[self.object.column]

    def get_form_class(self):
        return get_filter_form(self.parent_fk, self.column_type)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = [(col, col) for col in self.schema]
        return kwargs

    def form_valid(self, form: forms.Form) -> HttpResponse:
        form.instance.type = IBIS_TO_TYPE[self.column_type.name]
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("filters:update", args=(self.object.id,))


class FilterDelete(DeleteView):
    template_name = "filters/delete.html"
    model = Filter

    def get_success_url(self) -> str:
        return reverse("filters:list")
