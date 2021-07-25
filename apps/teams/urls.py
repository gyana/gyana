from apps.utils.access import login_and_permission_to_access
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import path

from . import views
from .models import Team
from .roles import user_can_access_team


def user_is_member(user, pk, *args, **kwargs):
    team = get_object_or_404(Team, pk=pk)
    return user_can_access_team(user, team)


login_and_team_required = login_and_permission_to_access(user_is_member)


app_name = "teams"

urlpatterns = [
    path("new/", login_required(views.TeamCreate.as_view()), name="create"),
    path(
        "<hashid:pk>",
        login_and_team_required(views.TeamDetail.as_view()),
        name="detail",
    ),
    path(
        "<hashid:pk>/update",
        login_and_team_required(views.TeamUpdate.as_view()),
        name="update",
    ),
    path(
        "<hashid:pk>/delete",
        login_and_team_required(views.TeamDelete.as_view()),
        name="delete",
    ),
    path(
        "<hashid:pk>/members",
        login_and_team_required(views.TeamMembers.as_view()),
        name="members",
    ),
]
