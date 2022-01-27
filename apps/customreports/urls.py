from django.urls import path

from . import frames, views

app_name = "customreports"
connector_urlpatterns = (
    [
        path("", frames.FacebookAdsCustomReportList.as_view(), name="list"),
        path("new", views.FacebookAdsCustomReportCreate.as_view(), name="create"),
        path(
            "<hashid:pk>/update",
            frames.FacebookAdsCustomReportUpdate.as_view(),
            name="update",
        ),
        path(
            "<hashid:pk>/delete",
            views.FacebookAdsCustomReportDelete.as_view(),
            name="delete",
        ),
    ],
    "connectors_customreports",
)
