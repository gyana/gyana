from django.urls import path

from . import views

app_name = "nodes"
urlpatterns = [
    path("", views.NodeList.as_view(), name="list"),
    path("new", views.NodeCreate.as_view(), name="create"),
    path("<hashid:pk>", views.NodeDetail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.NodeUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.NodeDelete.as_view(), name="delete"),
]
