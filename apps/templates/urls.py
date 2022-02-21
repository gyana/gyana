from django.urls import path

from apps.projects.access import login_and_project_required
from apps.teams.access import login_and_team_required

from . import views

app_name = "templates"
urlpatterns = []

project_urlpatterns = (
    [
        path(
            "",
            login_and_project_required(views.TemplateInstanceList.as_view()),
            name="list",
        ),
        path(
            "<hashid:pk>",
            login_and_project_required(views.TemplateInstanceUpdate.as_view()),
            name="update",
        ),
    ],
    "project_templateinstances",
)

team_urlpatterns = (
    [
        path("", login_and_team_required(views.TemplateList.as_view()), name="list"),
        path(
            "<hashid:template_id>",
            login_and_team_required(views.TemplateInstanceCreate.as_view()),
            name="create",
        ),
    ],
    "team_templates",
)
