from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "description",
        "team",
    ]
    readonly_fields = ["id", "team", "periodic_task"]
    fields = readonly_fields + ["name", "description"]
