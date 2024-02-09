import pytest

from apps.base.forms import ModelForm
from apps.tables.widgets import TableSelect
from apps.widgets.forms import WidgetSourceForm

pytestmark = pytest.mark.django_db


def test_table_select_basic(project, dashboard_factory, integration_table_factory, pwf):
    dashboard = dashboard_factory(project=project)
    table = integration_table_factory(project=project)

    form = WidgetSourceForm(dashboard=dashboard)

    pwf.render(form)

    assert False

    # TODO: write tests within new framework


# def test_input_node_search(with_pg_trgm_extension, client, setup):
#     table, workflow = setup
#     r = client.post(
#         "/nodes/api/nodes/",
#         data={"kind": "input", "workflow": workflow.id, "x": 0, "y": 0},
#     )
#     assert r.status_code == 201
#     input_node = Node.objects.first()
#     assert input_node is not None

#     r = client.post(
#         f"/nodes/{id}", data={"submit": "Save & Preview", **{"search": "olympia"}}
#     )
#     r = client.get(f"/nodes/{input_node.id}")
#     assertSelectorText(r, "label.checkbox", "olympia")
#     assertSelectorLength(r, "label.checkbox", 1)
