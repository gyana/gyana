from apps.base.frames import TurboFrameFormsetUpdateView, TurboFrameUpdateView
from apps.base.analytics import NODE_UPDATED_EVENT, track_node
from apps.base.table_data import get_table
from apps.base.templates import template_exists
from django import forms
from django.http.response import HttpResponse
from django.urls import reverse
from django_tables2.config import RequestConfig
from django_tables2.tables import Table
from django_tables2.views import SingleTableMixin
from turbo_response.views import TurboFrameTemplateView

from .bigquery import get_query_from_node
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

    def get_formset_kwargs(self, formset):

        if formset.get_default_prefix() in [
            "add_columns",
            "rename_columns",
            "edit_columns",
            "aggregations",
            "filters",
            "formula_columns",
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
        context["show_docs"] = self.request.GET.get("show_docs", False) == "true" or (
            self.object.data_updated is None
            and self.object.kind not in ["union", "intersect"]
        )

        # Node-specific documentation
        help_template = f"nodes/help/{self.object.kind}.html"
        context["help_template"] = (
            help_template
            if template_exists(help_template)
            else "nodes/help/default.html"
        )

        # Node-specific form templates
        form_template = f"nodes/forms/{self.object.kind}.html"
        context["form_template"] = (
            form_template
            if template_exists(form_template)
            else "nodes/forms/default.html"
        )

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
        return context

    def get_form_class(self):
        return KIND_TO_FORM[self.object.kind]

    def get_form(self):
        if self.object.kind == Node.Kind.INPUT or self.object.parents.first():
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


class NodeGrid(SingleTableMixin, TurboFrameTemplateView):
    template_name = "nodes/grid.html"
    paginate_by = 15
    turbo_frame_dom_id = "workflows-grid"

    def get_context_data(self, **kwargs):
        self.node = Node.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["node"] = self.node
        error_template = f"nodes/errors/{self.node.error}.html"
        if template_exists(error_template):
            context["error_template"] = error_template
        return context

    def get_table(self, **kwargs):
        try:
            table = get_table(
                self.node.schema, get_query_from_node(self.node), **kwargs
            )

            return RequestConfig(
                self.request, paginate=self.get_table_pagination(table)
            ).configure(table)
        except Exception as err:
            # We have to return
            return type("DynamicTable", (Table,), {})(data=[])
