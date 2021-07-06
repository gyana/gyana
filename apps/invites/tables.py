import django_tables2 as tables

from apps.utils.table import NaturalDatetimeColumn

from .models import Invite


class InviteTable(tables.Table):
    class Meta:
        model = Invite
        attrs = {"class": "table"}
        fields = ("email", "role", "sent", "status")

    email = tables.Column(linkify=True)

    sent = NaturalDatetimeColumn()
