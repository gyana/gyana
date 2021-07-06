from django.urls import path

from . import views

app_name = "integrations"
urlpatterns = [
    path("<hashid:pk>/grid", views.IntegrationGrid.as_view(), name="grid"),
    path("<hashid:pk>/sync", views.IntegrationSync.as_view(), name="sync"),
    path(
        "<hashid:pk>/authorize", views.IntegrationAuthorize.as_view(), name="authorize"
    ),
    path(
        "<hashid:pk>/authorize-fivetran",
        views.authorize_fivetran,
        name="authorize-fivetran",
    ),
    path(
        "<hashid:pk>/authorize-fivetran-redirect",
        views.authorize_fivetran_redirect,
        name="authorize-fivetran-redirect",
    ),
    path("<str:session_key>/generate-signed-url", views.generate_signed_url),
    path("<str:session_key>/start-sync", views.start_sync),
]

project_urlpatterns = (
    [
        path("", views.IntegrationList.as_view(), name="list"),
        path("new", views.IntegrationCreate.as_view(), name="create"),
        path("upload", views.IntegrationUpload.as_view(), name="upload"),
        path("<hashid:pk>", views.IntegrationDetail.as_view(), name="detail"),
        path("<hashid:pk>/update", views.IntegrationUpdate.as_view(), name="update"),
        path("<hashid:pk>/delete", views.IntegrationDelete.as_view(), name="delete"),
        path(
            "<hashid:pk>/structure",
            views.IntegrationStructure.as_view(),
            name="structure",
        ),
        path("<hashid:pk>/data", views.IntegrationData.as_view(), name="data"),
        path(
            "<hashid:pk>/settings", views.IntegrationSettings.as_view(), name="settings"
        ),
        path(
            "<hashid:pk>/sheet-verify",
            views.IntegrationDetail.as_view(),
            name="sheet-verify",
        ),
    ],
    "project_integrations",
)
