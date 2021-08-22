from apps.connectors.models import Connector
from apps.sheets.models import Sheet
from apps.uploads.models import Upload
from django.contrib import admin

from .models import Integration


class ConnectorInline(admin.StackedInline):
    model = Connector


class SheetInline(admin.StackedInline):
    model = Sheet


class UploadInline(admin.StackedInline):
    model = Upload
    fields = ["file_gcs_path", "field_delimiter"]
    readonly_fields = ["file_gcs_path"]


KIND_TO_INLINE = {
    Integration.Kind.CONNECTOR: ConnectorInline,
    Integration.Kind.SHEET: SheetInline,
    Integration.Kind.UPLOAD: UploadInline,
}


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "project",
        "kind",
        "state",
    )
    list_filter = ["kind", "state"]
    search_fields = ["id", "name", "project"]
    fields = ["project", "kind", "name", "state", "ready"]
    readonly_fields = ["project", "kind"]

    def get_inlines(self, request, obj):
        return [KIND_TO_INLINE[obj.kind]]

    # This will help you to disbale add functionality
    def has_add_permission(self, request):
        return False
