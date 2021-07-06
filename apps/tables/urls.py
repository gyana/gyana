from django.urls import path

from . import views

app_name = "tables"
urlpatterns = [
    path("", views.TableList.as_view(), name="list"),
    path("new", views.TableCreate.as_view(), name="create"),
    path("<hashid:pk>", views.TableDetail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.TableUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.TableDelete.as_view(), name="delete"),
]
