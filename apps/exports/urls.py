from django.urls import path

from . import frames
from .access import login_and_node_required, login_and_table_required

app_name = "exports"
urlpatterns = [
    path(
        "new/node/<int:parent_id>",
        login_and_node_required(frames.ExportCreateNode.as_view()),
        name="create_node",
    ),
    path(
        "new/integration_table/<int:parent_id>",
        login_and_table_required(frames.ExportCreateIntegrationTable.as_view()),
        name="create_integration_table",
    ),
    path("<int:pk>/download", frames.ExportDownload.as_view(), name="download"),
]
