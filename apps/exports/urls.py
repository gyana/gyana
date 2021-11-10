from django.urls import path

from . import frames

app_name = "exports"
urlpatterns = [
    path(
        "new/node/<int:parent_id>",
        frames.ExportCreateNode.as_view(),
        name="create_node",
    ),
    path(
        "new/integration_table/<int:parent_id>",
        frames.ExportCreateIntegrationTable.as_view(),
        name="create_integration_table",
    ),
]
