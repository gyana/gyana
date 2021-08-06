from django.urls import path

from . import views

app_name = "connectors"
urlpatterns = [
    path("", views.ConnectorList.as_view(), name="list"),
    path("new", views.ConnectorCreate.as_view(), name="create"),
    path("<hashid:pk>", views.ConnectorDetail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.ConnectorUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.ConnectorDelete.as_view(), name="delete"),
]
