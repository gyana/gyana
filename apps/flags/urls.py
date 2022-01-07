from django.urls import path

from apps.teams.access import login_and_admin_required

from . import views

app_name = "flags"
team_urlpatterns = (
    [
        path("", login_and_admin_required(views.TeamFlags.as_view()), name="team"),
    ],
    "team_flags",
)
