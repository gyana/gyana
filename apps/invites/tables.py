import django_tables2 as tables
from django.utils.safestring import mark_safe

from apps.utils.table import NaturalDatetimeColumn

from .models import Invite


class InviteTable(tables.Table):
    class Meta:
        model = Invite
        attrs = {"class": "table"}
        fields = ("email", "role")

    email = tables.Column(linkify=True)

    resend = tables.TemplateColumn(template_name="invites/resend.html")
