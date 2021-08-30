from apps.teams.access import login_and_team_required
from django.urls import path

from . import views

app_name = "templates"
urlpatterns = []

project_urlpatterns = (
    [
        path(
            "",
            # TODO: access limited to project
            views.TemplateInstanceList.as_view(),
            name="list",
        ),
        path(
            "<hashid:pk>",
            # TODO: access limited to project
            views.TemplateInstanceUpdate.as_view(),
            name="detail",
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
