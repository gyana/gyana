from apps.teams.access import login_and_team_required
from django.urls import path

from . import frames, views

app_name = "templates"

urlpatterns = [
    path(
        "<hashid:pk>",
        frames.TemplateInstanceSetup.as_view(),
        name="setup",
    ),
]

team_urlpatterns = (
    [
        path("", login_and_team_required(views.TemplateList.as_view()), name="list"),
        path(
            "<hashid:template_id>",
            views.TemplateInstanceCreate.as_view(),
            name="create",
        ),
    ],
    "team_templates",
)
