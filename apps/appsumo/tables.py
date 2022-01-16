import django_tables2 as tables
from apps.base.tables import NaturalDatetimeColumn

from .models import AppsumoCode, AppsumoExtra


class AppsumoCodeTable(tables.Table):
    class Meta:
        model = AppsumoCode
        attrs = {"class": "table"}
        fields = ("code", "deal", "redeemed", "redeemed_by", "refunded")

    refunded = tables.Column(orderable=False)
    redeemed = NaturalDatetimeColumn()


class AppsumoExtraTable(tables.Table):
    class Meta:
        model = AppsumoExtra
        attrs = {"class": "table"}
        fields = ("rows", "reason")
