from django.urls import path

from . import views

app_name = "cypress"
urlpatterns = [
    path(
        "resetdb",
        views.resetdb,
        name="resetdb",
    ),
    path("outbox", views.outbox, name="outbox"),
    path("periodic", views.periodic, name="periodic"),
    path("vcr/start", views.start_vcr, name="start_vcr"),
    path("vcr/stop", views.start_vcr, name="stop_vcr"),
]
