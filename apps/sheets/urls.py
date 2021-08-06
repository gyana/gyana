from django.urls import path

from . import views

app_name = "sheets"
urlpatterns = [
    path("", views.SheetList.as_view(), name="list"),
    path("new", views.SheetCreate.as_view(), name="create"),
    path("<hashid:pk>", views.SheetDetail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.SheetUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.SheetDelete.as_view(), name="delete"),
]
