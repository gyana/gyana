import django_tables2 as tables

from .models import Invite


class InviteTable(tables.Table):
    class Meta:
        model = Invite
        attrs = {"class": "table"}
        fields = ("email", "role")

    email = tables.Column(linkify=True)

    resend = tables.TemplateColumn(template_name="invites/resend.html")
