from django.db.models import F
from django.urls import reverse
from django.views.generic import DetailView, TemplateView, UpdateView
from django_tables2 import MultiTableMixin

from apps.nodes.models import Node
from apps.projects.mixins import ProjectMixin
from apps.runs.tables import JobRunTable
from apps.workflows.tables import ReferenceTable

from .forms import WorkflowNameForm, WorkflowSettingsForm
from .models import Workflow


class WorkflowOverview(ProjectMixin, TemplateView):
    template_name = "workflows/overview.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        integrations = self.project.integration_set
        workflows = self.project.workflow_set
        results = (
            Node.objects.filter(workflow__project=self.project, kind=Node.Kind.OUTPUT)
            .exclude(table=None)
            .count()
        )
        nodes = Node.objects.filter(workflow__project=self.project)
        incomplete = workflows.filter(state=Workflow.State.INCOMPLETE).count()
        outdated = workflows.filter(
            last_success_run__started_at__lte=F("data_updated")
        ).count()
        failed = workflows.filter(state=Workflow.State.FAILED).count()

        context_data["workflows"] = {
            "all": workflows.order_by("-updated").all()[:5],
            "total": workflows.count(),
            "results": results,
            "nodes": nodes.count(),
            "incomplete": incomplete,
            "outdated": outdated,
            "failed": failed,
            "operational": incomplete + outdated + failed == 0,
        }

        context_data["integrations"] = {"ready": integrations.ready().count()}

        return context_data


class WorkflowLastRun(DetailView):
    template_name = "workflows/last_run.html"
    model = Workflow


class WorkflowSettings(ProjectMixin, MultiTableMixin, UpdateView):
    template_name = "workflows/settings.html"
    model = Workflow
    form_class = WorkflowSettingsForm
    tables = [JobRunTable, ReferenceTable]
    paginate_by = 10

    def get_tables_data(self):
        return [self.object.runs.all(), self.object.used_in]

    def get_success_url(self) -> str:
        return reverse(
            "project_workflows:settings", args=(self.project.id, self.object.id)
        )


class WorkflowName(UpdateView):
    template_name = "workflows/name.html"
    model = Workflow
    form_class = WorkflowNameForm

    def get_success_url(self) -> str:
        return reverse("workflows:name", args=(self.object.id,))
