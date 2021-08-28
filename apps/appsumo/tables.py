import django_tables2 as tables
from apps.base.table import NaturalDatetimeColumn

from .models import AppsumoCode


class AppsumoCodeTable(tables.Table):
    class Meta:
        model = AppsumoCode
        attrs = {"class": "table"}
        fields = ("code", "redeemed", "redeemed_by", "refunded")

    redeemed = NaturalDatetimeColumn()
