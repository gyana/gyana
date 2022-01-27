import django_tables2 as tables

from apps.base.tables import NaturalDatetimeColumn

from .models import FacebookAdsCustomReport


class FacebookAdsCustomReportTable(tables.Table):
    class Meta:
        model = FacebookAdsCustomReport
        attrs = {"class": "table"}
        fields = ("table_name",)

    table_name = tables.Column()
