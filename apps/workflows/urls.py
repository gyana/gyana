from apps.projects.access import login_and_project_required
from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404
from django.urls import path
from lib.decorators import login_and_permission_to_access

from . import views
from .models import Workflow


def workflow_of_team(user, pk, *args, **kwargs):
    workflow = get_object_or_404(Workflow, pk=pk)
    return user_can_access_team(user, workflow.project.team)


login_and_workflow_required = login_and_permission_to_access(workflow_of_team)

app_name = "workflows"
urlpatterns = [
    # html
    path(
        "<hashid:pk>/last_run",
        login_and_workflow_required(views.WorkflowLastRun.as_view()),
        name="last_run",
    ),
    # rest api
    path(
        "<int:pk>/run_workflow",
        login_and_workflow_required(views.workflow_run),
        name="run_workflow",
    ),
    path(
        "<int:pk>/out_of_date",
        login_and_workflow_required(views.worflow_out_of_date),
        name="worflow_out_of_date",
    ),
    path(
        "<hashid:pk>/duplicate",
        login_and_workflow_required(views.WorkflowDuplicate.as_view()),
        name="duplicate",
    ),
]


project_urlpatterns = (
    [
        path("", login_and_project_required(views.WorkflowList.as_view()), name="list"),
        path(
            "new",
            login_and_project_required(views.WorkflowCreate.as_view()),
            name="create",
        ),
        path(
            "<hashid:pk>",
            login_and_project_required(views.WorkflowDetail.as_view()),
            name="detail",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_project_required(views.WorkflowDelete.as_view()),
            name="delete",
        ),
    ],
    "project_workflows",
)
