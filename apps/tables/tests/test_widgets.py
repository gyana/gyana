import pytest

from apps.base.forms import ModelForm
from apps.tables.widgets import TableSelect
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


class TestForm(ModelForm):
    class Meta:
        model = Widget
        fields = ["table"]
        widgets = {"table": TableSelect(parent="dashboard")}

    def __init__(self, *args, **kwargs):
        self.dashboard = kwargs.pop("dashboard")
        super().__init__(*args, **kwargs)
        self.fields["table"].widget.parent_entity = self.dashboard


def test_table_select_basic(project, dashboard_factory, integration_table_factory, pwf):
    dashboard = dashboard_factory(project=project)
    table = integration_table_factory(project=project)

    form = TestForm(dashboard=dashboard)

    pwf.render(form)

    # TODO: write tests within new framework
