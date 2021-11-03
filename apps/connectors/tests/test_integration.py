import pytest
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.connectors.periodic import check_syncing_connectors_from_fivetran
from apps.integrations.models import Integration
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from .mock import get_mock_fivetran_connector, get_mock_list_tables, get_mock_schema

pytestmark = pytest.mark.django_db


def test_connector_create(client, logged_in_user, bigquery, fivetran, project_factory):

    project = project_factory(team=logged_in_user.teams.first())

    fivetran.create.return_value = {"fivetran_id": "fid", "schema": "sid"}
    fivetran.get_authorize_url.side_effect = (
        lambda c, r: f"http://fivetran.url?redirect_uri={r}"
    )
    schema_obj = get_mock_schema(1)  # connector with a single table
    fivetran.get_schemas.return_value = schema_obj
    bigquery.get_table().num_rows = 10
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
    assertRedirects(r, f"http://fivetran.url?redirect_uri={redirect_uri}")

    assert fivetran.create.call_count == 1
    assert fivetran.create.call_args.args == (
        "google_analytics",
        project.team.id,
    )
    assert connector.fivetran_id == "fid"
    assert connector.schema == "sid"

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

    assert fivetran.get_schemas.call_count == 1
    assert fivetran.get_schemas.call_args.args == (connector,)

    # fivetran initial sync request will happen on post
    fivetran.get.return_value = get_mock_fivetran_connector(
        connector, is_historical_sync=True
    )
    r = client.post(f"{DETAIL}/configure", data={"dataset_tables": ["table_1"]})
    assertRedirects(r, f"{DETAIL}/load")

    assert fivetran.update_schemas.call_count == 1
    assert fivetran.update_schemas.call_args.args == (connector, schema_obj)
    assert fivetran.start_initial_sync.call_count == 1
    assert fivetran.start_initial_sync.call_args.args == (connector,)

    r = client.get(f"{DETAIL}/load")
    assertOK(r)
    assertContains(r, "Google Analytics")
    assertLink(r, f"{LIST}/pending", "pending integrations")

    # the user leaves the page and periodic job runs in background
    fivetran.get.return_value = get_mock_fivetran_connector(connector)
    check_syncing_connectors_from_fivetran.delay()

    integration.refresh_from_db()
    assert integration.state == Integration.State.DONE
    assert integration.table_set.count() == 1

    fivetran.get.call_count == 3
    fivetran.get.call_args.args == (connector,)

    # checking back explicitly will also complete
    integration.state = Integration.State.LOAD
    integration.table_set.all().delete()
    integration.save()

    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    integration.refresh_from_db()
    assert integration.state == Integration.State.DONE

    # todo: email
    # assert len(mail.outbox) == 1


def test_connector_create_regression(
    logged_in_user,
    bigquery,
    fivetran,
    connector_factory,
):

    connector = connector_factory(
        integration__ready=False,
        integration__state=Integration.State.LOAD,
        integration__project__team=logged_in_user.teams.first(),
        fivetran_sync_started=timezone.now(),
    )
    integration = connector.integration

    fivetran.get.return_value = get_mock_fivetran_connector(connector)
    schema_obj = get_mock_schema(1)  # connector with a single table
    fivetran.get_schemas.return_value = schema_obj
    bigquery.get_table().num_rows = 10

    # test: state is not set to done until bigquery has tables

    # fivetran reports completed but bigquery is not ready
    bigquery.list_tables.return_value = get_mock_list_tables(0)
    check_syncing_connectors_from_fivetran.delay()

    integration.refresh_from_db()
    assert integration.state == Integration.State.LOAD
    assert integration.table_set.count() == 0

    # bigquery is not up to date
    bigquery.list_tables.return_value = get_mock_list_tables(1)
    check_syncing_connectors_from_fivetran.delay()

    integration.refresh_from_db()
    assert integration.state == Integration.State.DONE
    assert integration.table_set.count() == 1


def test_status_on_pending_page(
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
    )
    project = connector.integration.project

    schema_obj = get_mock_schema(1)
    fivetran.get_schemas.return_value = schema_obj
    fivetran.get.return_value = get_mock_fivetran_connector(
        connector, is_historical_sync=True
    )
    bigquery.get_table().num_rows = 10
    bigquery.list_tables.return_value = get_mock_list_tables(1)

    LIST = f"/projects/{project.id}/integrations"

    # test: the status indicator on the pending page will be loading, until the
    # connector has completed the sync

    # loading
    r = client.get_turbo_frame(
        f"{LIST}/pending",
        f"/connectors/{connector.id}/icon",
    )
    assertOK(r)
    assertSelectorLength(r, ".fa-circle-notch", 1)

    assert fivetran.get.call_count == 1
    assert fivetran.get.call_args.args == (connector,)
    fivetran.get.return_value = get_mock_fivetran_connector(connector)

    # done
    r = client.get_turbo_frame(
        f"{LIST}/pending",
        f"/connectors/{connector.id}/icon",
    )
    assertOK(r)
    assertSelectorLength(r, ".fa-exclamation-triangle", 1)

    assert fivetran.get.call_count == 2
    assert fivetran.get.call_args.args == (connector,)

    connector.integration.refresh_from_db()
    assert connector.integration.state == Integration.State.DONE


def test_update_tables_in_non_database(
    client,
    logged_in_user,
    fivetran,
    bigquery,
    connector_factory,
    integration_table_factory,
):
    connector = connector_factory(
        integration__project__team=logged_in_user.teams.first()
    )
    integration = connector.integration
    project = integration.project

    schema_obj = get_mock_schema(2)
    fivetran.get.return_value = get_mock_fivetran_connector(connector)
    fivetran.get_schemas.return_value = schema_obj
    bigquery.list_tables.return_value = get_mock_list_tables(2)

    for table in schema_obj.schemas[0].tables:
        integration_table_factory(
            bq_table=table.name_in_destination, project=project, integration=integration
        )

    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"

    # test: if the user removes tables in the configure form, those tables are
    # deleted

    assert integration.table_set.count() == 2

    # update the schema in fivetran
    r = client.get(f"{DETAIL}/configure")
    assertOK(r)
    assertFormRenders(r, ["name", "dataset_tables", "dataset_schema"])

    r = client.post(f"{DETAIL}/configure", data={"dataset_tables": ["table_1"]})
    assertRedirects(r, f"{DETAIL}/load", target_status_code=302)
    assert fivetran.update_schemas.call_count == 1
    schema_tables = fivetran.update_schemas.call_args.args[1].schemas[0].tables
    enabled_tables = [t for t in schema_tables if t.enabled]
    assert len(enabled_tables) == 1
    assert schema_tables[0].key == "table_1"

    # slightly hacky - this is working because the code mutates the mock schema object

    # remove those tables
    assert integration.table_set.count() == 1


def test_status_broken(client, logged_in_user, fivetran, connector_factory):

    connector = connector_factory(
        integration__project__team=logged_in_user.teams.first()
    )
    integration = connector.integration
    project = integration.project

    fivetran.get.return_value = get_mock_fivetran_connector(connector, is_broken=True)
    fivetran.get_authorize_url.side_effect = (
        lambda c, r: f"http://fivetran.url?redirect_uri={r}"
    )

    LIST = f"/projects/{project.id}/integrations"
    DETAIL = f"{LIST}/{integration.id}"

    # test: status is broken with link to re-authorize

    r = client.get_turbo_frame(f"{DETAIL}", f"/connectors/{connector.id}/status")
    assertOK(r)
    assertContains(r, "Your connector is broken.")
    redirect_uri = f"http://localhost:8000{LIST}/connectors/{connector.id}/authorize"
    assertLink(r, f"http://fivetran.url?redirect_uri={redirect_uri}", "fixing it")


def test_connector_search_and_categories(client, logged_in_user, project_factory):

    project = project_factory(team=logged_in_user.teams.first())

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
