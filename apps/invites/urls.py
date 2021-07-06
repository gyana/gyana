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
        path("<int:pk>/resend", views.InviteResend.as_view(), name="resend"),
    ],
    "team_invites",
)
