from apps.projects.access import login_and_project_required
from django.urls import path

from . import views

project_urlpatterns = (
    [
        path(
            "<hashid:pk>/delete",
            login_and_project_required(views.TableDelete.as_view()),
            name="delete",
        ),
    ],
    "project_tables",
)
