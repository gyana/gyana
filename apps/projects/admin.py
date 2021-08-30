from apps.templates.models import Template
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description", "team"]
    fields = ["id", "name", "description", "team"]
    readonly_fields = ["id"]

    @admin.action(description="Promote to template")
    def make_published(self, request, queryset):
        for project in queryset:
            template = Template(project=project)
            template.save()
