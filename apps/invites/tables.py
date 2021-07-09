from apps.utils.table import NaturalDatetimeColumn
import django_tables2 as tables
from django_tables2.utils import A

from .models import Invite


class InviteTable(tables.Table):
    class Meta:
        model = Invite
        attrs = {"class": "table"}
        fields = ("email", "sent", "role")

    email = tables.Column(linkify=True)
    sent = NaturalDatetimeColumn()

    resend = tables.TemplateColumn(template_name="invites/resend.html", verbose_name="Actions")
    # delete = tables.LinkColumn(
    #     viewname="team_invites:delete", args=(A("team__id"), A("id")), text="Delete"
    # )
