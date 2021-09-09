from apps.projects.access import login_and_project_required
from django.urls import path

from . import frames, rest, views
from .access import login_and_workflow_required

app_name = "workflows"
urlpatterns = [
    # views
    path(
        "<hashid:pk>/duplicate",
        login_and_workflow_required(views.WorkflowDuplicate.as_view()),
        name="duplicate",
    ),
    # rest
    path(
        "<int:pk>/run_workflow",
        login_and_workflow_required(rest.workflow_run),
        name="run_workflow",
    ),
    path(
        "<int:pk>/out_of_date",
        login_and_workflow_required(rest.workflow_out_of_date),
        name="worflow_out_of_date",
    ),
    # frames
    path(
        "<hashid:pk>/last_run",
        login_and_workflow_required(frames.WorkflowLastRun.as_view()),
        name="last_run",
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
        path(
            "overview",
            login_and_project_required(frames.WorkflowOverview.as_view()),
            name="overview",
        ),
    ],
    "project_workflows",
)
