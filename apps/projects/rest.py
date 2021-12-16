import analytics
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.base.analytics import PROJECT_RUN_EVENT

from .models import Project
from .tasks import run_project


@api_view(http_method_names=["POST"])
def project_run(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    graph_run = run_project(project, request.user)
    analytics.track(request.user.id, PROJECT_RUN_EVENT, {"id": project.id})
    return Response({"task_id": graph_run.task_id})
