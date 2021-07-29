import analytics
from apps.nodes.config import get_node_config_with_arity
from apps.projects.mixins import ProjectMixin
from apps.utils.segment_analytics import (
    WORFKLOW_RUN_EVENT,
    WORKFLOW_CREATED_EVENT,
    WORKFLOW_DUPLICATED_EVENT,
)
from django import forms
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from turbo_response.views import TurboCreateView, TurboUpdateView

from .bigquery import run_workflow
from .forms import WorkflowForm, WorkflowFormCreate
from .models import Workflow
from .tables import WorkflowTable

# CRUDL


class WorkflowList(ProjectMixin, SingleTableView):
    template_name = "workflows/list.html"
    model = Workflow
    table_class = WorkflowTable
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["workflow_count"] = Workflow.objects.filter(
            project=self.project
        ).count()
        return context

    def get_queryset(self) -> QuerySet:
        return Workflow.objects.filter(project=self.project).all()


class WorkflowCreate(ProjectMixin, TurboCreateView):
    template_name = "workflows/create.html"
    model = Workflow
    form_class = WorkflowFormCreate

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project

        return initial

    def get_success_url(self) -> str:
        return reverse(
            "project_workflows:detail", args=(self.project.id, self.object.id)
        )

    def form_valid(self, form: forms.Form) -> HttpResponse:
        r = super().form_valid(form)
        analytics.track(
            self.request.user.id,
            WORKFLOW_CREATED_EVENT,
            {"id": form.instance.id, "name": form.instance.name},
        )

        return r


class WorkflowDetail(ProjectMixin, TurboUpdateView):
    template_name = "workflows/detail.html"
    model = Workflow
    form_class = WorkflowForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nodes"] = get_node_config_with_arity()
        return context

    def get_success_url(self) -> str:
        return reverse(
            "project_workflows:detail", args=(self.project.id, self.object.id)
        )


class WorkflowDelete(ProjectMixin, DeleteView):
    template_name = "workflows/delete.html"
    model = Workflow

    def get_success_url(self) -> str:
        return reverse("project_workflows:list", args=(self.project.id,))


class WorkflowLastRun(DetailView):
    template_name = "workflows/last_run.html"
    model = Workflow


class WorkflowDuplicate(TurboUpdateView):
    template_name = "workflows/duplicate.html"
    model = Workflow
    fields = []

    def form_valid(self, form: forms.Form) -> HttpResponse:
        r = super().form_valid(form)
        analytics.track(
            self.request.user.id,
            WORKFLOW_DUPLICATED_EVENT,
            {
                "id": form.instance.id,
            },
        )

        clone = self.object.make_clone(
            attrs={"name": "Copy of " + self.object.name, "last_run": None}
        )

        node_map = {}

        nodes = self.object.nodes.all()
        # First create the mapping between original and cloned nodes
        for node in nodes:
            node_clone = node.make_clone()
            node_map[node] = node_clone
            clone.nodes.add(node_clone)

        # Then copy the relationships
        for node in nodes:
            node_clone = node_map[node]
            for parent in node.parents.iterator():
                node_clone.parents.add(node_map[parent])

        clone.save()
        return r

    def get_success_url(self) -> str:
        return reverse("project_workflows:list", args=(self.object.project.id,))


@api_view(http_method_names=["POST"])
def workflow_run(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    errors = run_workflow(workflow) or {}

    analytics.track(
        request.user.id,
        WORFKLOW_RUN_EVENT,
        {
            "id": workflow.id,
            "success": not bool(errors),
            **{f"error_{idx}": errors[key] for idx, key in enumerate(errors.keys())},
        },
    )

    return Response(errors)


@api_view(http_method_names=["GET"])
def worflow_out_of_date(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return Response(
        {
            "isOutOfDate": workflow.out_of_date,
            "hasBeenRun": workflow.last_run is not None,
        }
    )
