from apps.templates.models import Template
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description", "team", "is_template"]
    fields = ["id", "name", "description", "team"]
    readonly_fields = ["id"]
    actions = ["promote_to_template"]

    @admin.action(description="Promote to template")
    def promote_to_template(self, request, queryset):
        for project in queryset:
            if project.dashboard_set.count() == 0:
                self.message_user(request, f"Project {object.name} needs at least one dashboard")
                continue
            template = Template(project=project)
            template.save()

    @admin.display(boolean=True)
    def is_template(self, object):
        return object.is_template
