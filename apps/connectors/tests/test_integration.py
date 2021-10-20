from unittest.mock import MagicMock, Mock

import pytest
from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.connectors.fivetran import FivetranSchema
from apps.integrations.models import Integration
from apps.projects.models import Project
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table as BqTable
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db


def test_create(client, logged_in_user, bigquery_client, fivetran_client):

    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)

    # mock connector with a single table
    fivetran_client.create = lambda *_: {"fivetran_id": "fid", "schema": "sid"}
    fivetran_client.authorize = lambda c, r: f"http://fivetran.url?redirect_uri={r}"
    fivetran_client.has_completed_sync = lambda *_: True
    fivetran_client.block_until_synced = lambda *_: None
    table = {
        "name_in_destination": "table",
        "enabled": True,
        "enabled_patch_settings": {"allowed": True},
    }
    schema = FivetranSchema(
        key="schema",
        name_in_destination="dataset",
        enabled=True,
        tables={"table": table},
    )
    fivetran_client.get_schemas = lambda *_: [schema]
    bigquery_client.list_tables = lambda *_: [
        BqTable(
            "project.dataset.table",
            schema=[
                SchemaField(column, type_)
                for column, type_ in [("name", "STRING"), ("age", "INTEGER")]
            ],
        )
    ]
    bigquery_client.get_table().num_rows = 10

    # create a new connector, configure it and complete the sync

    # view all connectors
    r = client.get(f"/projects/{project.id}/integrations/connectors/new")
    assertOK(r)
    assertLink(
        r,
        f"/projects/{project.id}/integrations/connectors/new?service=google_analytics",
        "Google Analytics",
    )

    # create
    r = client.get(
        f"/projects/{project.id}/integrations/connectors/new?service=google_analytics",
    )
    assertOK(r)
    assertFormRenders(r, [])

    r = client.post(
        f"/projects/{project.id}/integrations/connectors/new?service=google_analytics",
        data={},
    )

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.CONNECTOR
    assert integration.connector is not None
    assert integration.created_by == logged_in_user
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    redirect_uri = f"http://localhost:8000/projects/{project.id}/integrations/connectors/{integration.connector.id}/authorize"
    assertRedirects(r, f"http://fivetran.url?redirect_uri={redirect_uri}")

    # authorize redirect
    r = client.get(
        f"/projects/{project.id}/integrations/connectors/{integration.connector.id}/authorize"
    )
    assertRedirects(r, f"{INTEGRATION_URL}/configure")

    # configure
    r = client.get(f"{INTEGRATION_URL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "dataset_schema", "dataset_tables"])

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(f"{INTEGRATION_URL}/configure")
    assertRedirects(r, f"{INTEGRATION_URL}/load")

    r = client.get(f"{INTEGRATION_URL}/load")
    assertRedirects(r, f"{INTEGRATION_URL}/done")

    assert integration.table_set.count() == 1

    # todo: email
    # assert len(mail.outbox) == 1
