import pytest
from django import forms
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertOK, assertSelectorLength
from apps.connectors.models import Connector
from apps.connectors.tests.mock import get_mock_fivetran_connector
from apps.customreports.models import FacebookAdsCustomReport

pytestmark = pytest.mark.django_db


def test_customreports_crudl(client, project, connector_factory, fivetran):
    connector = connector_factory(integration__project=project, service="facebook_ads")
    integration = connector.integration
    fivetran.get_schemas.return_value = {}

    CONFIGURE = f"/projects/{project.id}/integrations/{integration.id}/configure"
    LIST = f"/connectors/{connector.id}/customreports"

    # list
    r = client.get_turbo_frame(CONFIGURE, f"{LIST}/")
    assertOK(r)
    assertFormRenders(r, [])

    # create
    r = client.post(f"{LIST}/new")
    assertRedirects(r, f"{LIST}/", status_code=303)

    assert FacebookAdsCustomReport.objects.count() == 1
    customreport = FacebookAdsCustomReport.objects.first()

    DETAIL = f"{LIST}/{customreport.id}"

    # update
    r = client.get(f"{DETAIL}/update")
    assertOK(r)
    assertFormRenders(
        r,
        [
            "table_name",
            "fields",
            "breakdowns",
            "action_breakdowns",
            "aggregation",
            "action_report_time",
            "click_attribution_window",
            "view_attribution_window",
            "use_unified_attribution_setting",
            "initial-fields",
        ],
    )

    r = client.post(
        f"{DETAIL}/update",
        data={**forms.model_to_dict(customreport), "table_name": "Renamed"},
    )
    assertRedirects(r, f"{DETAIL}/update", status_code=303)

    customreport.refresh_from_db()
    assert customreport.table_name == "Renamed"

    r = client.get_turbo_frame(CONFIGURE, f"{LIST}/")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)

    # delete
    r = client.post(f"{DETAIL}/delete")
    assertRedirects(r, f"{LIST}/")

    assert FacebookAdsCustomReport.objects.count() == 0


def test_customreports_import(
    client, project, connector_factory, facebook_ads_custom_report_factory, fivetran
):

    connector = connector_factory(integration__project=project)
    integration = connector.integration
    fivetran.get_schemas.return_value = {}
    fivetran.get.return_value = get_mock_fivetran_connector(
        is_historical_sync=True, service="facebook_ads"
    )

    CONFIGURE = f"/projects/{project.id}/integrations/{integration.id}/configure"
    data = {"setup_mode": Connector.SetupMode.ADVANCED, "submit": True}

    # connector import
    client.post(CONFIGURE, data=data)

    assert fivetran.update.call_count == 0
    assert fivetran.test.call_count == 0

    connector.service = "facebook_ads"
    connector.save()

    client.post(CONFIGURE, data=data)
    assert fivetran.update.call_count == 0
    assert fivetran.test.call_count == 0

    facebook_ads_custom_report = facebook_ads_custom_report_factory(connector=connector)

    # only called when service has custom reports
    client.post(CONFIGURE, data=data)
    assert fivetran.update.call_count == 1
    assert fivetran.update.call_args.args == (connector,)
    assert fivetran.test.call_count == 1
    assert fivetran.test.call_args.args == (connector,)
