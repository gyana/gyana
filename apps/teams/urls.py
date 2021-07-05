from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "teams"

urlpatterns = [
    path("<int:pk>", views.TeamDetail.as_view(), name="detail"),
    path("<int:pk>/members", views.TeamMembers.as_view(), name="members"),
    path("<int:pk>/settings", views.TeamUpdate.as_view(), name="settings"),
    path("<int:pk>/delete", views.TeamDelete.as_view(), name="delete"),
    path("<int:team_id>/invite", views.TeamInvite.as_view(), name="invite"),
    path("create/", views.TeamCreate.as_view(), name="create_team"),
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
]

team_urlpatterns = (
    [
        # path("", views.manage_team_react, name="manage_team_react"),
        # path("manage", views.manage_team, name="manage_team"),
        path(
            "resend-invite/<slug:invitation_id>/",
            views.resend_invitation,
            name="resend_invitation",
        ),
    ],
    "single_team",
)


# drf config
# router = routers.DefaultRouter()
# router.register("api/teams", views.TeamViewSet)
# urlpatterns += router.urls

# single_team_router = routers.DefaultRouter()
# single_team_router.register("api/invitations", views.InvitationViewSet)
# team_urlpatterns[0].extend(single_team_router.urls)
