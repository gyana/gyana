from django.urls import path

from apps.projects.access import login_and_project_required

from . import views

app_name = "schedules"
urlpatterns = []


project_urlpatterns = (
    [
        path(
            "",
            login_and_project_required(views.ScheduleDetail.as_view()),
            name="detail",
        ),
        path(
            "settings",
            login_and_project_required(views.ScheduleSettings.as_view()),
            name="settings",
        ),
    ],
    "project_schedule",
)
