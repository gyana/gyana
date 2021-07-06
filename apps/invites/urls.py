from django.urls import path

from . import views

app_name = "invites"
team_urlpatterns = (
    [
        path("", views.InviteList.as_view(), name="list"),
        path("new", views.InviteCreate.as_view(), name="create"),
        path("<hashid:pk>", views.InviteDetail.as_view(), name="detail"),
        path("<hashid:pk>/update", views.InviteUpdate.as_view(), name="update"),
        path("<hashid:pk>/delete", views.InviteDelete.as_view(), name="delete"),
        path("<hashid:pk>/resend", views.InviteResend.as_view(), name="resend"),
    ],
    "team_invites",
)
