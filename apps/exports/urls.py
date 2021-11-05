from django.urls import path

from . import frames, views

app_name = "exports"
urlpatterns = [
    path("", views.ExportList.as_view(), name="list"),
    path("new/<int:parent_id>", frames.ExportCreate.as_view(), name="create"),
    path("<hashid:pk>", views.ExportDetail.as_view(), name="detail"),
    path("<hashid:pk>/update", views.ExportUpdate.as_view(), name="update"),
    path("<hashid:pk>/delete", views.ExportDelete.as_view(), name="delete"),
]
