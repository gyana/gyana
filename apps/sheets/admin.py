from django.contrib import admin

from .models import Sheet


class SheetInline(admin.StackedInline):
    model = Sheet
    fields = ["id", "url", "cell_range", "drive_file_last_modified_at_sync"]
    readonly_fields = ["id", "url", "drive_file_last_modified_at_sync"]

    def has_delete_permission(self, request, obj):
        return False
