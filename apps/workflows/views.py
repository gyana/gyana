import json
from functools import cached_property

import inflection
from apps.projects.mixins import ProjectMixin
from apps.workflows.table_data import BigQueryTableData
from django import forms
from django.db import transaction
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView
from django_tables2 import Column, SingleTableView, Table
from django_tables2.config import RequestConfig
from django_tables2.views import SingleTableMixin
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from turbo_response.views import TurboCreateView, TurboUpdateView

from .bigquery import run_workflow
from .forms import KIND_TO_FORM, KIND_TO_FORMSETS, WorkflowForm
from .models import Node, NodeConfig, Workflow
from .serializers import NodeSerializer
from .tables import WorkflowTable

# CRUDL


class WorkflowList(ProjectMixin, SingleTableView):
    template_name = "workflows/list.html"
    model = Workflow
    table_class = WorkflowTable
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["workflow_count"] = Workflow.objects.filter(
            project=self.project
        ).count()

        return context_data

    def get_queryset(self) -> QuerySet:
        return Workflow.objects.filter(project=self.project).all()


class WorkflowCreate(ProjectMixin, TurboCreateView):
    template_name = "workflows/create.html"
    model = Workflow
    form_class = WorkflowForm

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project
        return initial

    def get_success_url(self) -> str:
        return reverse(
            "projects:workflows:detail", args=(self.project.id, self.object.id)
        )


class WorkflowDetail(ProjectMixin, DetailView):
    template_name = "workflows/detail.html"
    model = Workflow

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nodes"] = NodeConfig
        return context


class WorkflowUpdate(ProjectMixin, TurboUpdateView):
    template_name = "workflows/update.html"
    model = Workflow
    form_class = WorkflowForm

    def get_success_url(self) -> str:
        return reverse(
            "projects:workflows:detail", args=(self.project.id, self.object.id)
        )


class WorkflowDelete(ProjectMixin, DeleteView):
    template_name = "workflows/delete.html"
    model = Workflow

    def get_success_url(self) -> str:
        return reverse("projects:workflows:list", args=(self.project.id,))


# Nodes


class NodeViewSet(viewsets.ModelViewSet):
    serializer_class = NodeSerializer
    queryset = Node.objects.all()
    filterset_fields = ["workflow"]


class NodeUpdate(TurboUpdateView):
    template_name = "workflows/node.html"
    model = Node

    @cached_property
    def workflow(self):
        return Workflow.objects.get(pk=self.kwargs["workflow_id"])

    @cached_property
    def formsets(self):
        return KIND_TO_FORMSETS.get(self.object.kind, [])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workflow"] = self.workflow
        context["node"] = self.object

        for formset in self.formsets:
            context[inflection.underscore(formset.__name__)] = (
                formset(self.request.POST, instance=self.object)
                if self.request.POST
                else formset(instance=self.object)
            )

        context["preview_node_id"] = int(
            self.request.GET.get("preview_node_id", self.object.id)
        )

        return context

    def form_valid(self, form: forms.Form) -> HttpResponse:
        context = self.get_context_data()

        if self.formsets:
            with transaction.atomic():
                self.object = form.save()
                for formset_cls in self.formsets:
                    formset = context[inflection.underscore(formset_cls.__name__)]
                    if formset.is_valid():
                        formset.instance = self.object
                        formset.save()

        return super().form_valid(form)

    def get_form_class(self):
        return KIND_TO_FORM[self.object.kind]

    def get_success_url(self) -> str:
        base_url = reverse("workflows:node", args=(self.workflow.id, self.object.id))
        if "save-preview" in self.request.POST:
            preview_node_id = self.get_context_data()["preview_node_id"]
            return f"{base_url}?preview_node_id={preview_node_id}&preview=true"
        return base_url


class NodeGrid(SingleTableMixin, TemplateView):
    template_name = "workflows/grid.html"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        self.node = Node.objects.get(id=kwargs["pk"])
        return super().get_context_data(**kwargs)

    def get_table(self, **kwargs):
        """Dynamically creates a table class and adds the correct table data

        See https://django-tables2.readthedocs.io/en/stable/_modules/django_tables2/views.html
        """
        # Inspired by https://stackoverflow.com/questions/16696066/django-tables2-dynamically-adding-columns-to-table-not-adding-attrs-to-table
        attrs = {name: Column() for name in self.node.schema}
        attrs["Meta"] = type("Meta", (), {"attrs": {"class": "table"}})
        table_class = type("DynamicTable", (Table,), attrs)

        table_data = BigQueryTableData(self.node.get_query())

        table = table_class(data=table_data, **kwargs)

        return RequestConfig(
            self.request, paginate=self.get_table_pagination(table)
        ).configure(table)


@api_view(http_method_names=["POST"])
def workflow_run(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    errors = run_workflow(workflow)
    return Response(errors or {})
