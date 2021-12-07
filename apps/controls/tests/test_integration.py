import uuid
from datetime import date
from unittest.mock import Mock

import pandas as pd
import pytest
from pytest_django.asserts import assertContains
from turbo_response.response import TurboStreamResponse

from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import PickableMock, mock_bq_client_with_schema
from apps.controls.models import Control, CustomChoice
from apps.dashboards.models import Dashboard
from apps.filters.models import DateRange
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


INPUT_DATA = [
    {
        "count": 1,
        "athlete": "Meng",
        "birthday": date(year=1986, month=8, day=21),
    },
]


def mock_bq_client_data(bigquery):
    def side_effect(query, **kwargs):
        mock = PickableMock()
        mock.rows_df = pd.DataFrame(INPUT_DATA)
        mock.total_rows = len(INPUT_DATA)
        return mock

    bigquery.get_query_results = Mock(side_effect=side_effect)


def test_control_crudl(
    client, project, dashboard_factory, bigquery, integration_table_factory
):
    mock_bq_client_with_schema(
        bigquery, [(name, type_.name) for name, type_ in TABLE.schema().items()]
    )
    mock_bq_client_data(bigquery)
    # add a widget with a dateslice column so it's picked up when creating the output stream
    dashboard = dashboard_factory(project=project)
    widget = dashboard.widget_set.create(
        date_column="birthday",
        dimension="athlete",
        kind=Widget.Kind.COLUMN,
        table=integration_table_factory(project=project),
    )
    control_url = f"/projects/{project.id}/dashboards/{dashboard.id}/controls/"
    # create
    r = client.post(control_url + "new", data={"dashboard_id": dashboard.id})

    assertOK(r)
    control = Control.objects.first()
    assert isinstance(r, TurboStreamResponse)
    assert control is not None
    assertContains(r, "controls:create-stream")

    # update
    r = client.get(control_url + f"{control.id}/update")
    assertOK(r)
    assertFormRenders(r, ["date_range"])

    r = client.post(
        control_url + f"{control.id}/update", data={"date_range": CustomChoice.CUSTOM}
    )
    assert r.status_code == 422
    assertFormRenders(r, ["date_range", "start", "end"])

    r = client.post(
        control_url + f"{control.id}/update",
        data={"date_range": CustomChoice.CUSTOM, "submit": "submit"},
    )
    assertOK(r)
    control.refresh_from_db()
    assert isinstance(r, TurboStreamResponse)
    assertContains(r, "controls:update-stream")

    # is sending the widget output
    assertContains(r, f"widgets-output-{widget.id}-stream")
    assert control.date_range == CustomChoice.CUSTOM

    # delete
    r = client.delete(control_url + f"{control.id}/delete")
    assert Control.objects.first() is None


def test_public_date_slice_not_updating(
    client, project, dashboard_factory, control_factory
):
    """Tests that on submission on a public dashboard the control is not
    actually updating"""
    dashboard = dashboard_factory(
        project=project,
        shared_status=Dashboard.SharedStatus.PUBLIC,
        shared_id=uuid.uuid4(),
    )
    control = control_factory(dashboard=dashboard)
    r = client.post(
        f"/projects/{project.id}/dashboards/{dashboard.id}/controls/{control.id}/update-public",
        data={"date_range": CustomChoice.CUSTOM, "submit": "submit"},
    )
    assertOK(r)
    assert isinstance(r, TurboStreamResponse)

    control.refresh_from_db()
    assert control.date_range == DateRange.THIS_YEAR
