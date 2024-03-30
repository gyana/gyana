import uuid
from datetime import date

import pandas as pd
import pytest

from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.controls.models import Control, ControlWidget, CustomChoice
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


def test_control_crudl(
    client, project, dashboard_factory, integration_table_factory, engine
):
    engine.set_data(pd.DataFrame(INPUT_DATA))
    # add a widget with a dateslice column so it's picked up when creating the output stream
    dashboard = dashboard_factory(project=project)
    page = dashboard.pages.create()
    page.widgets.create(
        date_column="birthday",
        dimension="athlete",
        kind=Widget.Kind.COLUMN,
        table=integration_table_factory(project=project),
    )
    control_url = f"/projects/{project.id}/dashboards/{dashboard.id}/controls/"
    # create
    r = client.post(control_url + "new-widget", data={"page": page.id, "x": 0, "y": 0})

    assertOK(r)
    control = Control.objects.first()
    control_widget = ControlWidget.objects.first()
    assert control is not None
    assert control_widget is not None

    # update
    r = client.get(control_url + f"{control.id}/update-widget")
    assertOK(r)
    assertFormRenders(r, ["date_range", "start", "end"])

    r = client.post(
        control_url + f"{control.id}/update-widget",
        data={"date_range": CustomChoice.CUSTOM},
    )
    assertOK(r)

    r = client.post(
        control_url + f"{control.id}/update-widget",
        data={"date_range": CustomChoice.CUSTOM, "submit": "submit"},
    )
    assertOK(r)
    control.refresh_from_db()

    # todo: check it is sending the HX-Trigger event

    # delete
    r = client.post(control_url + f"{control_widget.id}/delete-widget")
    assert r.status_code == 302
    assert Control.objects.first() is None
    assert ControlWidget.objects.first() is None


def test_public_date_slice_not_updating(
    client, project, dashboard_factory, control_factory, control_widget_factory
):
    """Tests that on submission on a public dashboard the control is not
    actually updating"""
    dashboard = dashboard_factory(
        project=project,
        shared_status=Dashboard.SharedStatus.PUBLIC,
        shared_id=uuid.uuid4(),
    )
    dashboard.pages.create()
    page = dashboard.pages.first()
    control = control_factory(page=page)
    control_widget_factory(page=page, control=control)

    r = client.post(
        f"/projects/{project.id}/dashboards/{dashboard.id}/controls/{control.id}/update-public",
        data={"date_range": CustomChoice.CUSTOM, "submit": "submit"},
    )
    assertOK(r)

    control.refresh_from_db()
    assert control.date_range == DateRange.THIS_YEAR


def test_adding_more_control_widgets(
    client, project, dashboard_factory, control_factory
):
    dashboard = dashboard_factory(project=project)
    page = dashboard.pages.create()
    control = control_factory(page=page)
    control_widget = control.widgets.create(page=page)

    control_url = f"/projects/{project.id}/dashboards/{dashboard.id}/controls/"
    # create 2nd widget doesnt create new control
    r = client.post(f"{control_url}new-widget", data={"page": page.id, "x": 0, "y": 0})

    assertOK(r)
    assert ControlWidget.objects.count() == 2
    assert Control.objects.count() == 1

    # deleting the first widget doesnt delete control
    r = client.post(f"{control_url}{ControlWidget.objects.first().id}/delete-widget")
    assert r.status_code == 302
    assert ControlWidget.objects.count() == 1
    assert Control.objects.first() is not None

    r = client.post(f"{control_url}{ControlWidget.objects.first().id}/delete-widget")
    assert r.status_code == 302
    assert ControlWidget.objects.first() is None
    assert Control.objects.first() is None
