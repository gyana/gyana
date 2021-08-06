from django.urls import path

from . import frames

app_name = "sheets"
urlpatterns = [
    path("<hashid:pk>/sync", frames.IntegrationSync.as_view(), name="sync"),
]
