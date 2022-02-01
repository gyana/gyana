from django.urls import path

from . import frames, views
from .access import login_and_customreport_required

app_name = "customreports"
connector_urlpatterns = (
    [
        path(
            "",
            login_and_customreport_required(
                frames.FacebookAdsCustomReportList.as_view()
            ),
            name="list",
        ),
        path(
            "new",
            login_and_customreport_required(
                views.FacebookAdsCustomReportCreate.as_view()
            ),
            name="create",
        ),
        path(
            "<hashid:pk>/update",
            login_and_customreport_required(
                frames.FacebookAdsCustomReportUpdate.as_view()
            ),
            name="update",
        ),
        path(
            "<hashid:pk>/delete",
            login_and_customreport_required(
                views.FacebookAdsCustomReportDelete.as_view()
            ),
            name="delete",
        ),
    ],
    "connectors_customreports",
)
