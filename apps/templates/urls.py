from apps.teams.access import login_and_team_required
from django.urls import path

from . import views

app_name = "templates"
urlpatterns = []


team_urlpatterns = (
    [
        path("", login_and_team_required(views.TemplateList.as_view()), name="list"),
        # path("new", views.TemplateCreate.as_view(), name="create"),
        # path("<hashid:pk>", views.TemplateDetail.as_view(), name="detail"),
        # path("<hashid:pk>/update", views.TemplateUpdate.as_view(), name="update"),
        # path("<hashid:pk>/delete", views.TemplateDelete.as_view(), name="delete"),
    ],
    "team_templates",
)
