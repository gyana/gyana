from django.urls import include, path

from apps.invites import urls as invite_urls

from . import views

app_name = "teams"

urlpatterns = [
    path("create/", views.TeamCreate.as_view(), name="create_team"),
    path("<int:pk>", views.TeamDetail.as_view(), name="detail"),
    path("<int:pk>/members", views.TeamMembers.as_view(), name="members"),
    path("<int:pk>/settings", views.TeamUpdate.as_view(), name="settings"),
    path("<int:pk>/delete", views.TeamDelete.as_view(), name="delete"),
    path("<int:team_id>/invites/", include(invite_urls.team_urlpatterns)),
]
