import django_tables2 as tables

from apps.base.table import NaturalDatetimeColumn

from .models import OAuth2


class OAuth2Table(tables.Table):
    class Meta:
        model = OAuth2
        attrs = {"class": "table"}
        fields = ("name", "scope", "is_authorized", "created")

    name = tables.Column(linkify=True)
    is_authorized = tables.BooleanColumn(verbose_name="Authorized")
    created = NaturalDatetimeColumn()
    actions = tables.TemplateColumn(
        template_name="oauth2/actions.html", verbose_name="Actions", orderable=False
    )
