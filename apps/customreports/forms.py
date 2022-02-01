from apps.base.forms import BaseModelForm

from .models import FacebookAdsCustomReport


class FacebookAdsCustomReportCreateForm(BaseModelForm):
    class Meta:
        model = FacebookAdsCustomReport
        fields = []

    def __init__(self, *args, **kwargs):
        self._connector = kwargs.pop("connector")
        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.connector = self._connector


class FacebookAdsCustomReportUpdateForm(BaseModelForm):
    class Meta:
        model = FacebookAdsCustomReport
        fields = [
            "table_name",
            "fields",
            "breakdowns",
            "action_breakdowns",
            "aggregation",
            "action_report_time",
            "click_attribution_window",
            "view_attribution_window",
            "use_unified_attribution_setting",
        ]
