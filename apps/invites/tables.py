import django_tables2 as tables
from django_tables2.utils import A

from apps.base.table import NaturalDatetimeColumn

from .models import Invite


class InviteTable(tables.Table):
    class Meta:
        model = Invite
        attrs = {"class": "table"}
        fields = ("email", "role", "sent")

    email = tables.Column(linkify=True)
    sent = NaturalDatetimeColumn()

    resend = tables.TemplateColumn(
        template_name="invites/resend.html", verbose_name="Actions", orderable=False
    )
    # delete = tables.LinkColumn(
    #     viewname="team_invites:delete", args=(A("team__id"), A("id")), text="Delete"
    # )
