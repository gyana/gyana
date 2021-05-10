from django.urls import path

from .. import views

app_name = "datasets"
urlpatterns = [
    path("", views.DatasetList.as_view(), name="list"),
    path("new", views.DatasetCreate.as_view(), name="create"),
    path("<int:pk>", views.DatasetDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.DatasetUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.DatasetDelete.as_view(), name="delete"),
    path("<int:pk>/structure", views.DatasetStructure.as_view(), name="structure"),
    path("<int:pk>/data", views.DatasetData.as_view(), name="data"),
    path("<int:pk>/settings", views.DatasetSettings.as_view(), name="settings"),
]
