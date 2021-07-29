from django.urls import path

from apps.teams.access import login_and_admin_required

from . import views

app_name = "invites"
team_urlpatterns = (
    [
        path("", login_and_admin_required(views.InviteList.as_view()), name="list"),
        path(
            "new", login_and_admin_required(views.InviteCreate.as_view()), name="create"
        ),
        path(
            "<hashid:pk>",
            login_and_admin_required(views.InviteDetail.as_view()),
            name="detail",
        ),
        path(
            "<hashid:pk>/update",
            login_and_admin_required(views.InviteUpdate.as_view()),
            name="update",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_admin_required(views.InviteDelete.as_view()),
            name="delete",
        ),
        path(
            "<hashid:pk>/resend",
            login_and_admin_required(views.InviteResend.as_view()),
            name="resend",
        ),
    ],
    "team_invites",
)
