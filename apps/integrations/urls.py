from django.urls import path

from . import views

app_name = "integrations"
urlpatterns = [
    path("<int:pk>/grid", views.IntegrationGrid.as_view(), name="grid"),
    path("<int:pk>/sync", views.IntegrationSync.as_view(), name="sync"),
    path("<int:pk>/authorize", views.IntegrationAuthorize.as_view(), name="authorize"),
    path(
        "<int:pk>/authorize-fivetran",
        views.authorize_fivetran,
        name="authorize-fivetran",
    ),
    path(
        "<int:pk>/authorize-fivetran-redirect",
        views.authorize_fivetran_redirect,
        name="authorize-fivetran-redirect",
    ),
    path("<int:pk>/generate-signed-url", views.generate_signed_url),
    path("<int:pk>/start-sync", views.start_sync),
]

project_urlpatterns = (
    [
        path("", views.IntegrationList.as_view(), name="list"),
        path("new", views.IntegrationCreate.as_view(), name="create"),
        path("upload", views.IntegrationUpload.as_view(), name="upload"),
        path("<int:pk>", views.IntegrationDetail.as_view(), name="detail"),
        path("<int:pk>/update", views.IntegrationUpdate.as_view(), name="update"),
        path("<int:pk>/delete", views.IntegrationDelete.as_view(), name="delete"),
        path(
            "<int:pk>/structure", views.IntegrationStructure.as_view(), name="structure"
        ),
        path("<int:pk>/data", views.IntegrationData.as_view(), name="data"),
        path("<int:pk>/settings", views.IntegrationSettings.as_view(), name="settings"),
        path(
            "<int:pk>/sheet-verify",
            views.IntegrationDetail.as_view(),
            name="sheet-verify",
        ),
    ],
    "project_integrations",
)
