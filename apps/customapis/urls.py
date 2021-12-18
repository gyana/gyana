from django.urls import path

from apps.projects.access import login_and_project_enabled_required

from . import views
from .access import login_and_customapi_required

app_name = "customapis"

urlpatterns = [
    path(
        "<hashid:pk>/oauth2/login",
        views.CustomAPIOAuth2Login.as_view(),
        name="oauth2_login",
    ),
    path(
        "<hashid:pk>/oauth2/callback",
        views.CustomAPIOAuth2Callback.as_view(),
        name="oauth2_callback",
    ),
]


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
