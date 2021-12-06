from django.db.models import F
from django.urls import reverse

from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameTemplateView,
    TurboFrameUpdateView,
)
from apps.nodes.models import Node
from apps.projects.mixins import ProjectMixin

from .forms import WorkflowSettingsForm
from .models import Workflow


class WorkflowOverview(ProjectMixin, TurboFrameTemplateView):
    template_name = "workflows/overview.html"
    turbo_frame_dom_id = "workflows:overview"

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
        incomplete = workflows.filter(last_run=None).count()
        outdated = workflows.filter(last_run__lte=F("data_updated")).count()
        failed = nodes.exclude(error=None).values_list("workflow").distinct().count()

        context_data["workflows"] = {
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


class WorkflowLastRun(TurboFrameDetailView):
    template_name = "workflows/last_run.html"
    model = Workflow
    turbo_frame_dom_id = "workflow-last-run"


class WorkflowSettings(ProjectMixin, TurboFrameUpdateView):
    template_name = "workflows/settings.html"
    model = Workflow
    form_class = WorkflowSettingsForm
    turbo_frame_dom_id = "workflows:settings"

    def get_success_url(self) -> str:
        return reverse(
            "project_workflows:settings", args=(self.project.id, self.object.id)
        )
