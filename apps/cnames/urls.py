from django.urls import path

from apps.teams.access import login_and_team_required

from . import frames, views
from .access import login_and_cname_required

app_name = "cnames"

urlpatterns = [
    path(
        "<hashid:pk>/status",
        login_and_cname_required(frames.CNameStatus.as_view()),
        name="status",
    ),
]


team_urlpatterns = (
    [
        path("", login_and_team_required(frames.CNameList.as_view()), name="list"),
        path(
            "new", login_and_team_required(views.CNameCreate.as_view()), name="create"
        ),
        path(
            "<hashid:pk>/delete",
            login_and_team_required(views.CNameDelete.as_view()),
            name="delete",
        ),
    ],
    "team_cnames",
)
