from django.urls import path

from apps.projects.access import login_and_project_enabled_required

from . import views

app_name = "customapis"

integration_urlpatterns = (
    [
        path(
            "new",
            login_and_project_enabled_required(views.CustomApiCreate.as_view()),
            name="create",
        ),
    ],
    "project_integrations_customapis",
)
