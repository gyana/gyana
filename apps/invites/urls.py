from django.urls import path

from . import views

app_name = "invites"
team_urlpatterns = (
    [
        path("", views.InviteList.as_view(), name="list"),
        path("new", views.InviteCreate.as_view(), name="create"),
        path("<int:pk>", views.InviteDetail.as_view(), name="detail"),
        path("<int:pk>/update", views.InviteUpdate.as_view(), name="update"),
        path("<int:pk>/delete", views.InviteDelete.as_view(), name="delete"),
    ],
    "team_invites",
)

urlpatterns = [
    path(
        "invitation/<slug:invitation_id>/",
        views.accept_invitation,
        name="accept_invitation",
    ),
    path(
        "invitation/<slug:invitation_id>/confirm/",
        views.accept_invitation_confirm,
        name="accept_invitation_confirm",
    ),
    path(
        "resend-invite/<slug:invitation_id>/",
        views.resend_invitation,
        name="resend_invitation",
    ),
]
