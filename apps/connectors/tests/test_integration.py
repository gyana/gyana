import pytest
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.base.tests.factory import (
    ConnectorFactory,
    IntegrationTableFactory,
    ProjectFactory,
)
from apps.connectors.fivetran.schema import FivetranSchema
from apps.integrations.models import Integration
from pytest_django.asserts import assertContains, assertRedirects

pytestmark = pytest.mark.django_db


def get_mock_schema(num_tables):
    tables = {
        f"table_{n}": {
            "name_in_destination": f"table_{n}",
            "enabled": True,
            "enabled_patch_settings": {"allowed": True},
        }
        for n in range(1, num_tables + 1)
    }
    schema = FivetranSchema(
        key="schema",
        name_in_destination="dataset",
        enabled=True,
        tables=tables,
    )
    return schema


def test_create(client, logged_in_user, bigquery_client, fivetran_client):

    project = ProjectFactory()

    fivetran_client.create.return_value = {"fivetran_id": "fid", "schema": "sid"}
    fivetran_client.get_authorize_url.side_effect = (
        lambda c, r: f"http://fivetran.url?redirect_uri={r}"
    )
    fivetran_client.has_completed_sync.return_value = False
    schema = get_mock_schema(1)  # connector with a single table
    fivetran_client.get_schemas.return_value = [schema]
    bigquery_client.get_table().num_rows = 10

    CONNECTORS_URL = f"/projects/{project.id}/integrations/connectors"

    # test: create a new connector, authorize it, configure it, start the sync,
    # view the load screen and finally complete the sync
    # at each step, verify that the fivetran client is called with correct variables
    # and mock the return

    # view all connectors
    r = client.get(f"{CONNECTORS_URL}/new")
    assertOK(r)
    assertLink(r, f"{CONNECTORS_URL}/new?service=google_analytics", "Google Analytics")

    # create
    r = client.get(f"{CONNECTORS_URL}/new?service=google_analytics")
    assertOK(r)
    assertFormRenders(r, [])

    r = client.post(f"{CONNECTORS_URL}/new?service=google_analytics", data={})
    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.CONNECTOR
    connector = integration.connector
    assert connector is not None
    assert integration.created_by == logged_in_user

    redirect_uri = f"http://localhost:8000{CONNECTORS_URL}/{connector.id}/authorize"
    assertRedirects(r, f"http://fivetran.url?redirect_uri={redirect_uri}")

    assert fivetran_client.create.call_count == 1
    assert fivetran_client.create.call_args.args == (
        "google_analytics",
        project.team.id,
    )
    assert connector.fivetran_id == "fid"
    assert connector.schema == "sid"

    assert fivetran_client.get_authorize_url.call_count == 1
    assert fivetran_client.get_authorize_url.call_args.args == (
        connector,
        redirect_uri,
    )

    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    # authorize redirect
    r = client.get(f"{CONNECTORS_URL}/{connector.id}/authorize")
    assertRedirects(r, f"{INTEGRATION_URL}/configure")

    # configure
    fivetran_client.get_schemas.reset_mock()
    r = client.get(f"{INTEGRATION_URL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "dataset_schema", "dataset_tables"])

    assert fivetran_client.get_schemas.call_count == 1
    assert fivetran_client.get_schemas.call_args.args == (connector,)

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(f"{INTEGRATION_URL}/configure")
    assertRedirects(r, f"{INTEGRATION_URL}/load")

    assert fivetran_client.update_schemas.call_count == 1
    assert fivetran_client.update_schemas.call_args.args == (connector, [schema])
    assert fivetran_client.start_initial_sync.call_count == 1
    assert fivetran_client.start_initial_sync.call_args.args == (connector,)

    r = client.get(f"{INTEGRATION_URL}/load")
    assertOK(r)
    assertContains(r, "Google Analytics")
    assertLink(
        r, f"/projects/{project.id}/integrations/pending", "pending integrations"
    )

    fivetran_client.has_completed_sync.return_value = True

    r = client.get(f"{INTEGRATION_URL}/load")
    assertRedirects(r, f"{INTEGRATION_URL}/done")

    fivetran_client.has_completed_sync.call_count == 3
    fivetran_client.has_completed_sync.call_args.args == (connector,)

    assert integration.table_set.count() == 1
    integration.refresh_from_db()
    assert integration.state == Integration.State.DONE

    # todo: email
    # assert len(mail.outbox) == 1


def test_status_on_pending_page(
    client, logged_in_user, bigquery_client, fivetran_client
):
    connector = ConnectorFactory(
        integration__ready=False, integration__state=Integration.State.LOAD
    )
    project = connector.integration.project

    schema = get_mock_schema(1)
    fivetran_client.get_schemas.return_value = [schema]
    fivetran_client.has_completed_sync.return_value = False
    bigquery_client.get_table().num_rows = 10

    # test: the status indicator on the pending page will be loading, until the
    # connector has completed the sync

    # loading
    r = client.get_turbo_frame(
        f"/projects/{project.id}/integrations/pending",
        f"/connectors/{connector.id}/icon",
    )
    assertOK(r)
    assertSelectorLength(r, ".fa-circle-notch", 1)

    assert fivetran_client.has_completed_sync.call_count == 1
    assert fivetran_client.has_completed_sync.call_args.args == (connector,)
    fivetran_client.has_completed_sync.return_value = True

    # done
    r = client.get_turbo_frame(
        f"/projects/{project.id}/integrations/pending",
        f"/connectors/{connector.id}/icon",
    )
    assertOK(r)
    assertSelectorLength(r, ".fa-exclamation-triangle", 1)

    assert fivetran_client.has_completed_sync.call_count == 2
    assert fivetran_client.has_completed_sync.call_args.args == (connector,)

    connector.integration.refresh_from_db()
    assert connector.integration.state == Integration.State.DONE


def test_update_tables_in_non_database(client, logged_in_user, fivetran_client):
    connector = ConnectorFactory()
    integration = connector.integration
    project = integration.project

    schema = get_mock_schema(2)
    fivetran_client.get_schemas.return_value = [schema]

    for table in schema.tables:
        IntegrationTableFactory(bq_table=table.name_in_destination)

    # test: if the user removes tables in the configure form, those tables are
    # deleted

    assert integration.table_set.count() == 2

    # update the schema in fivetran
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"
    r = client.get(f"{INTEGRATION_URL}/configure")
    assertOK(r)
    assertFormRenders(r, ["name", "dataset_tables", "dataset_schema"])

    r = client.post(
        f"{INTEGRATION_URL}/configure", data={"dataset_tables": ["table_1"]}
    )
    assertRedirects(r, f"{INTEGRATION_URL}/load", target_status_code=302)
    assert fivetran_client.update_schemas.call_count == 1
    assert len(fivetran_client.update_schemas.call_args.args[1][0].tables) == 1
    assert (
        fivetran_client.update_schemas.call_args.args[1][0].tables[0].key == "table_1"
    )

    # slightly hacky - this is working because the code mutates the mock schema object

    # remove those tables
    assert integration.table_set.count() == 1
