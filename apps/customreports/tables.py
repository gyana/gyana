import django_tables2 as tables

from .models import FacebookAdsCustomReport


class FacebookAdsCustomReportTable(tables.Table):
    class Meta:
        model = FacebookAdsCustomReport
        attrs = {"class": "table"}
        fields = ("table_name",)

    table_name = tables.Column()
    actions = tables.TemplateColumn(
        template_name="customreports/actions.html",
        verbose_name="Actions",
        orderable=False,
    )
