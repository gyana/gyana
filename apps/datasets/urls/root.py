from django.urls import path

from .. import views

app_name = "datasets"
urlpatterns = [
    path("<int:pk>/grid", views.DatasetGrid.as_view(), name="grid"),
    path("<int:pk>/sync", views.DatasetSync.as_view(), name="sync"),
    path("<int:pk>/authorize", views.DatasetAuthorize.as_view(), name="authorize"),
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
