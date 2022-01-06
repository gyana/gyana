from django.urls import path

from . import frames

app_name = "flags"
team_urlpatterns = (
    [
        path("", frames.TeamFlags.as_view(), name="team"),
    ],
    "team_flags",
)
