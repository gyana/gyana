from django.urls import path

from . import views

app_name = "cypress"
urlpatterns = [
    path(
        "resetdb",
        views.resetdb,
        name="resetdb",
    ),
]
