import pytest
from django.core import mail
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.connectors import periodic
from apps.integrations.models import Integration

from .mock import get_mock_fivetran_connector, get_mock_list_tables, get_mock_schema

pytestmark = pytest.mark.django_db


def test_connector_create(client, logged_in_user, bigquery, fivetran, project):
    fivetran.get_authorize_url.side_effect = (
        lambda c, r: f"http://fivetran.url?redirect_uri={r}"
    )
    schema_obj = get_mock_schema(1)  # connector with a single table
    fivetran.get_schemas.return_value = schema_obj.to_dict()
    fivetran.create.return_value = get_mock_fivetran_connector(is_historical_sync=True)
    bigquery.list_tables.return_value = get_mock_list_tables(1)

    LIST = f"/projects/{project.id}/integrations"
    CONNECTORS = f"{LIST}/connectors"

    # test: create a new connector, authorize it, configure it, start the sync,
    # view the load screen and finally complete the sync
    # at each step, verify that the fivetran client is called with correct variables
    # and mock the return

    # view all connectors
    r = client.get(f"{CONNECTORS}/new")
    assertOK(r)
    assertLink(r, f"{CONNECTORS}/new?service=google_analytics", "Google Analytics")

    # create
    r = client.get(f"{CONNECTORS}/new?service=google_analytics")
    assertOK(r)
    assertFormRenders(r, [])

    r = client.post(f"{CONNECTORS}/new?service=google_analytics", data={})
    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.CONNECTOR
    connector = integration.connector
    assert connector is not None
    assert integration.created_by == logged_in_user

    redirect_uri = f"http://localhost:8000{CONNECTORS}/{connector.id}/authorize"
    authorization_uri = f"http://fivetran.url?redirect_uri={redirect_uri}"
    assertRedirects(r, authorization_uri)

    assert fivetran.create.call_count == 1
    assert fivetran.create.call_args.args == (
        "google_analytics",
        project.team.id,
        "00:00",
    )
    assert connector.fivetran_id == "fivetran_id"
    assert connector.schema == "dataset"

    assert fivetran.get_authorize_url.call_count == 1
    assert fivetran.get_authorize_url.call_args.args == (
        connector,
        redirect_uri,
    )

    DETAIL = f"{LIST}/{integration.id}"

    # authorize redirect
    r = client.get(f"{CONNECTORS}/{connector.id}/authorize")
    assertRedirects(r, f"{DETAIL}/configure")

    # configure
    fivetran.get_schemas.reset_mock()
    r = client.get(f"{DETAIL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "dataset_schema", "dataset_tables"])
    assertLink(r, authorization_uri, "authorization")

    assert fivetran.get_schemas.call_count == 1
    assert fivetran.get_schemas.call_args.args == (connector,)

    # fivetran initial sync request will happen on post
    fivetran.get.return_value = get_mock_fivetran_connector(is_historical_sync=True)
    r = client.post(f"{DETAIL}/configure", data={"dataset_tables": ["table_1"]})
    assertRedirects(r, f"{DETAIL}/load")

    assert fivetran.update_schemas.call_count == 1
    assert fivetran.update_schemas.call_args.args == (connector, schema_obj.to_dict())
    assert fivetran.start_initial_sync.call_count == 1
    assert fivetran.start_initial_sync.call_args.args == (connector,)

    r = client.get(f"{DETAIL}/load")
    assertOK(r)
    assertContains(r, "Google Analytics")
    assertLink(r, f"{LIST}/", "integrations")

    # the user leaves the page and periodic job runs in background
    fivetran.get.return_value = get_mock_fivetran_connector(succeeded_at=timezone.now())
    fivetran.list.return_value = [
        get_mock_fivetran_connector(succeeded_at=timezone.now())
    ]
    periodic.sync_all_updates_from_fivetran.delay()

    integration.refresh_from_db()
    assert integration.state == Integration.State.DONE
    assert integration.table_set.count() == 1

    fivetran.get.call_count == 3
    fivetran.get.call_args.args == (connector,)

    assert len(mail.outbox) == 1

    # checking back explicitly will also complete
    fivetran.get.return_value = get_mock_fivetran_connector(succeeded_at=timezone.now())
    integration.state = Integration.State.LOAD
    integration.table_set.all().delete()
    integration.save()

    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    integration.refresh_from_db()
    assert integration.state == Integration.State.DONE


def test_status_on_integrations_page(
    client,
    logged_in_user,
    bigquery,
    fivetran,
    connector_factory,
):
    connector = connector_factory(
        integration__ready=False,
        integration__state=Integration.State.LOAD,
        integration__project__team=logged_in_user.teams.first(),
        schema_config=get_mock_schema(1).to_dict(),
        fivetran_sync_started=timezone.now(),
    )
    project = connector.integration.project

    fivetran.get.return_value = get_mock_fivetran_connector()
    bigquery.list_tables.return_value = get_mock_list_tables(1)

    LIST = f"/projects/{project.id}/integrations"

    # test: the status indicator on the integrations page will be loading, until the
    # connector has completed the sync

    # loading
    r = client.get_turbo_frame(
        f"{LIST}/",
        f"/connectors/{connector.id}/icon",
    )
    assertOK(r)
    assertSelectorLength(r, ".fa-circle-notch", 1)

    assert fivetran.get.call_count == 1
    assert fivetran.get.call_args.args == (connector,)
    fivetran.get.return_value = get_mock_fivetran_connector(succeeded_at=timezone.now())

    # done
    r = client.get_turbo_frame(
        f"{LIST}/",
        f"/connectors/{connector.id}/icon",
    )
    assertOK(r)
    assertSelectorLength(r, ".fa-info-circle", 1)

    assert fivetran.get.call_count == 2
    assert fivetran.get.call_args.args == (connector,)

    connector.integration.refresh_from_db()
    assert connector.integration.state == Integration.State.DONE


def test_status_broken(client, logged_in_user, fivetran, connector_factory):

    connector = connector_factory(
        integration__project__team=logged_in_user.teams.first()
    )
    integration = connector.integration
    project = integration.project

    fivetran.get.return_value = get_mock_fivetran_connector(is_broken=True)
    fivetran.get_authorize_url.side_effect = (
        lambda c, r: f"http://fivetran.url?redirect_uri={r}"
    )

    LIST = f"/projects/{project.id}/integrations"
    DETAIL = f"{LIST}/{integration.id}"

    # test: status is broken with link to re-authorize

    r = client.get_turbo_frame(f"{DETAIL}", f"/connectors/{connector.id}/status")
    assertOK(r)
    assertContains(r, "needs attention")
    redirect_uri = f"http://localhost:8000{LIST}/connectors/{connector.id}/authorize"
    assertLink(r, f"http://fivetran.url?redirect_uri={redirect_uri}", "needs attention")


def test_connector_search_and_categories(client, logged_in_user, project):

    LIST = f"/projects/{project.id}/integrations"
    CONNECTORS = f"{LIST}/connectors"

    # test: search and filter by category

    r = client.get(f"{CONNECTORS}/new")
    assertOK(r)
    assertLink(r, f"{CONNECTORS}/new?service=google_analytics", "Google Analytics")
    assertLink(r, f"{CONNECTORS}/new?service=asana", "Asana")

    # filter by category
    assertLink(r, f"{CONNECTORS}/new?category=Marketing", "Marketing")
    r = client.get(f"{CONNECTORS}/new?category=Marketing")
    assertOK(r)
    assertContains(r, "Google Analytics")
    assertNotContains(r, "Asana")

    # filter by search
    r = client.get(f"{CONNECTORS}/new?search=asa")
    assertOK(r)
    assertNotContains(r, "Google Analytics")
    assertContains(r, "Asana")
