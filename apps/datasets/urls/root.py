from django.urls import path

from .. import views

app_name = "datasets"
urlpatterns = [
    path("<int:pk>/grid", views.DatasetGrid.as_view(), name="grid"),
    path("<int:pk>/sync", views.DatasetSync.as_view(), name="sync"),
]
