from django.urls import path

from . import views

app_name = "workflows"
urlpatterns = [
    path("<hashid:pk>/run_workflow", views.workflow_run, name="run_workflow"),
    path(
        "<hashid:pk>/out_of_date", views.worflow_out_of_date, name="worflow_out_of_date"
    ),
    path("<hashid:pk>/last_run", views.WorkflowLastRun.as_view(), name="last_run"),
]


project_urlpatterns = (
    [
        path("", views.WorkflowList.as_view(), name="list"),
        path("new", views.WorkflowCreate.as_view(), name="create"),
        path("<hashid:pk>", views.WorkflowDetail.as_view(), name="detail"),
        path("<hashid:pk>/delete", views.WorkflowDelete.as_view(), name="delete"),
    ],
    "project_workflows",
)
