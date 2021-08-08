from django.urls import path

from . import frames, views

app_name = "sheets"
urlpatterns = [
    path("<hashid:pk>/progress", frames.SheetProgress.as_view(), name="progress"),
]

integration_urlpatterns = (
    [
        path("new", views.SheetCreate.as_view(), name="create"),
        path("<hashid:pk>", views.SheetDetail.as_view(), name="detail"),
    ],
    "project_integrations_sheets",
)
