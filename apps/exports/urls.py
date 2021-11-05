from django.urls import path

from . import frames

app_name = "exports"
urlpatterns = [
    path(
        "new/<str:parent_type>/<int:parent_id>",
        frames.ExportCreate.as_view(),
        name="create",
    ),
]
