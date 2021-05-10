from django.urls import path

from .. import views

app_name = "connectors"
urlpatterns = [
    path("<int:pk>/authorize", views.ConnectorAuthorize.as_view(), name="authorize"),
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
]
