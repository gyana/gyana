import analytics
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DeleteView, DetailView
from django_tables2 import SingleTableView

from apps.base.analytics import (
    WORKFLOW_CREATED_EVENT,
    WORKFLOW_CREATED_EVENT_FROM_INTEGRATION,
    WORKFLOW_DUPLICATED_EVENT,
)
from apps.base.views import TurboCreateView, TurboUpdateView
from apps.integrations.models import Integration
from apps.nodes.config import get_node_config_with_arity
from apps.nodes.models import Node
from apps.projects.mixins import ProjectMixin

from .forms import WorkflowFormCreate
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

    def form_valid(self, form):
        r = super().form_valid(form)
        analytics.track(
            self.request.user.id,
            WORKFLOW_CREATED_EVENT,
            {"id": form.instance.id, "name": form.instance.name},
        )

        return r


class WorkflowCreateFromIntegration(ProjectMixin, TurboCreateView):
    model = Workflow
    template_name = "workflows/create_from_integration.html"
    fields = ("project",)

    def get_success_url(self) -> str:
        return reverse(
            "project_workflows:detail", args=(self.project.id, self.object.id)
        )

    def form_valid(self, form):
        r = super().form_valid(form)
        analytics.track(
            self.request.user.id,
            WORKFLOW_CREATED_EVENT_FROM_INTEGRATION,
            {"id": form.instance.id, "name": form.instance.name},
        )
        integration = get_object_or_404(
            Integration, pk=self.request.POST["integration"]
        )
        table = integration.table_set.first()
        self.object.nodes.create(
            kind=Node.Kind.INPUT,
            name=f"Input from {integration.name}",
            input_table=table,
            x=0,
            y=0,
            has_been_saved=True,
            data_updated=timezone.now(),
        )
        self.object.name = f"{integration.name} workflow"
        self.object.name
        return r


class WorkflowDetail(ProjectMixin, DetailView):
    template_name = "workflows/detail.html"
    model = Workflow

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # copy dict because it's cached
        nodes = get_node_config_with_arity().copy()
        context["nodes"] = nodes
        context["sections"] = [
            "Table manipulations",
            "Column manipulations",
            "Annotation",
        ]
        return context


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

    def form_valid(self, form):
        r = super().form_valid(form)
        analytics.track(
            self.request.user.id,
            WORKFLOW_DUPLICATED_EVENT,
            {
                "id": form.instance.id,
            },
        )

        self.object.make_clone(
            attrs={
                "name": "Copy of " + self.object.name,
                "state": Workflow.State.INCOMPLETE,
            }
        )

        return r

    def get_success_url(self) -> str:
        return reverse("project_workflows:list", args=(self.object.project.id,))
