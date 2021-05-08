from django.urls import path

from . import views

app_name = "tables"
urlpatterns = [
    path("", views.TableList.as_view(), name="list"),
    path("new", views.TableCreate.as_view(), name="create"),
    path("<int:pk>", views.TableDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.TableUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.TableDelete.as_view(), name="delete"),
]
