from apps.base.analytics import NODE_UPDATED_EVENT, track_node
from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameFormsetUpdateView,
    TurboFrameUpdateView,
)
from apps.base.table_data import RequestConfig, get_table
from apps.base.templates import template_exists
from django import forms
from django.http.response import HttpResponse
from django.urls import reverse
from django_tables2.tables import Table
from django_tables2.views import SingleTableMixin

from .bigquery import NodeResultNone, get_query_from_node
from .forms import KIND_TO_FORM
from .models import Node


class NodeName(TurboFrameUpdateView):
    model = Node
    fields = ("name",)
    template_name = "nodes/name.html"
    turbo_frame_dom_id = "node-editable-title"

    def get_success_url(self) -> str:
        return reverse(
            "nodes:name",
            args=(self.object.id,),
        )


class NodeUpdate(TurboFrameFormsetUpdateView):
    template_name = "nodes/update.html"
    model = Node
    turbo_frame_dom_id = "workflow-modal"

    def get_formset_form_kwargs(self, formset):

        if formset.get_default_prefix() in [
            "add_columns",
            "rename_columns",
            "edit_columns",
            "aggregations",
            "filters",
            "formula_columns",
            "sort_columns",
            "window_columns",
        ]:
            return {"schema": self.object.parents.first().schema}

        return {}

    @property
    def preview_node_id(self):
        return int(self.request.GET.get("preview_node_id", self.object.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workflow"] = self.object.workflow
        context["preview_node_id"] = self.preview_node_id
        context["show_docs"] = self.request.GET.get("show_docs", False) == "true"

        # Node-specific documentation
        if self.object.kind == Node.Kind.FORMULA:
            context["help_template"] = "nodes/help/formula.html"

        # Add node type to list if it requires live updates
        context["do_live_updates"] = self.object.kind in [
            "pivot",
            "add",
            "edit",
            "aggregation",
            "filter",
            "unpivot",
            "window",
        ]
        context["parent_error_node"] = self.parent_error_node
        return context

    def get_form_class(self):
        return KIND_TO_FORM[self.object.kind]

    def get_form(self):
        is_input = self.object.kind == Node.Kind.INPUT
        has_parent = self.object.parents.first() is not None

        try:
            if not is_input and has_parent:
                get_query_from_node(self.object.parents.first())
            self.parent_error_node = None
        except NodeResultNone as e:
            self.parent_error_node = e.node

        if not self.parent_error_node and (is_input or has_parent):
            return super().get_form()

    def form_valid(self, form: forms.Form) -> HttpResponse:
        r = super().form_valid(form)
        track_node(self.request.user, form.instance, NODE_UPDATED_EVENT)
        return r

    def get_success_url(self) -> str:
        base_url = reverse("nodes:update", args=(self.object.id,))

        if self.request.POST.get("submit") == "Save & Preview":
            return f"{base_url}?preview_node_id={self.preview_node_id}"

        return base_url


class NodeGrid(SingleTableMixin, TurboFrameDetailView):
    template_name = "nodes/grid.html"
    model = Node
    paginate_by = 15
    turbo_frame_dom_id = "workflows-grid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        error_template = f"nodes/errors/{self.object.error}.html"
        if template_exists(error_template):
            context["error_template"] = error_template
        return context

    def get_table(self, **kwargs):
        try:
            query = get_query_from_node(self.object)
            table = get_table(self.object.schema, query, **kwargs)

            return RequestConfig(
                self.request, paginate=self.get_table_pagination(table)
            ).configure(table)
        except Exception as err:
            # We have to return
            return type("DynamicTable", (Table,), {})(data=[])
