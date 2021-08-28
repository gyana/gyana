from django.contrib import admin
from django.utils.html import format_html

from .models import Connector


class ConnectorInline(admin.StackedInline):
    model = Connector
    fields = [
        "id",
        "service",
        "fivetran_id",
        "schema",
        "fivetran_authorized",
        "fivetran_dashboard_url",
    ]
    readonly_fields = [
        "id",
        "service",
        "fivetran_id",
        "schema",
        "fivetran_dashboard_url",
    ]

    def fivetran_dashboard_url(self, instance):
        return format_html(
            '<a href="{0}" target="_blank">{1}</a>',
            instance.fivetran_dashboard_url,
            "Link",
        )

    def has_delete_permission(self, request, obj):
        return False
