from django.urls import path

from . import views

app_name = "cnames"

urlpatterns = []

team_urlpatterns = (
    [
        path("", views.CNameList.as_view(), name="list"),
        path("new", views.CNameCreate.as_view(), name="create"),
        path("<hashid:pk>", views.CNameDetail.as_view(), name="detail"),
        path("<hashid:pk>/update", views.CNameUpdate.as_view(), name="update"),
        path("<hashid:pk>/delete", views.CNameDelete.as_view(), name="delete"),
    ],
    "team_cnames",
)
