from django.contrib import admin

from .models import Upload


class UploadInline(admin.StackedInline):
    model = Upload
    fields = ["id", "file_gcs_path", "field_delimiter"]
    readonly_fields = ["id", "file_gcs_path"]

    def has_delete_permission(self, request, obj):
        return False
