from django.urls import path

from .. import views

app_name = "integrations"
urlpatterns = [
    path("", views.IntegrationList.as_view(), name="list"),
    path("new", views.IntegrationCreate.as_view(), name="create"),
    path("<int:pk>", views.IntegrationDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.IntegrationUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.IntegrationDelete.as_view(), name="delete"),
    path("<int:pk>/structure", views.IntegrationStructure.as_view(), name="structure"),
    path("<int:pk>/data", views.IntegrationData.as_view(), name="data"),
    path("<int:pk>/settings", views.IntegrationSettings.as_view(), name="settings"),
]
