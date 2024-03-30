from django.contrib import admin

from .models import Upload


class UploadInline(admin.StackedInline):
    model = Upload
    fields = ["id", "file", "field_delimiter"]
    readonly_fields = ["id", "file"]

    def has_delete_permission(self, request, obj):
        return False
