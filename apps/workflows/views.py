import analytics
from apps.base.analytics import WORKFLOW_CREATED_EVENT, WORKFLOW_DUPLICATED_EVENT
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.nodes.config import get_node_config_with_arity
from apps.nodes.models import Node
from apps.projects.mixins import ProjectMixin
from django import forms
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.urls import reverse
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView

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
        # copy dict because it's cached
        nodes = get_node_config_with_arity().copy()
        if not self.request.user.is_superuser:
            nodes.pop(Node.Kind.SENTIMENT)
        context["nodes"] = nodes
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


class WorkflowDuplicate(TurboUpdateView):
    template_name = "components/_duplicate.html"
    model = Workflow
    fields = []
    extra_context = {"object_name": "workflow"}

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
            node_clone = node.make_clone({"workflow": clone})
            node_map[node] = node_clone

        # Then copy the relationships
        for node in nodes:
            node_clone = node_map[node]
            for parent in node.parents.iterator():
                node_clone.parents.add(node_map[parent])

        return r

    def get_success_url(self) -> str:
        return reverse("project_workflows:list", args=(self.object.project.id,))
