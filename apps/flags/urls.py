from django.urls import path

from . import views

app_name = "flags"
team_urlpatterns = (
    [
        path("", views.TeamFlags.as_view(), name="team"),
    ],
    "team_flags",
)
