from apps.connectors.admin import ConnectorInline
from apps.sheets.admin import SheetInline
from apps.tables.admin import TableInline
from apps.uploads.admin import UploadInline
from django.contrib import admin

from .models import Integration

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
    fields = ["id", "project", "kind", "name", "state", "ready"]
    readonly_fields = ["id", "kind", "state"]

    def get_inlines(self, request, obj):
        return [KIND_TO_INLINE[obj.kind], TableInline]

    # This will help you to disbale add functionality
    def has_add_permission(self, request):
        return False
