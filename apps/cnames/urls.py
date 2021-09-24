from django.urls import path

from . import frames, views

app_name = "cnames"

urlpatterns = []

team_urlpatterns = (
    [
        path("", frames.CNameList.as_view(), name="list"),
        path("new", views.CNameCreate.as_view(), name="create"),
        path("<hashid:pk>/delete", views.CNameDelete.as_view(), name="delete"),
    ],
    "team_cnames",
)
