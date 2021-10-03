from unittest.mock import MagicMock, Mock

import pytest
from apps.base.clients import ibis_client
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.integrations.models import Integration
from apps.projects.models import Project
from apps.tables.models import Table
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table as BqTable
from pytest_django.asserts import assertContains, assertRedirects

pytestmark = pytest.mark.django_db


class PickableMock(Mock):
    def __reduce__(self):
        return (Mock, ())


def test_integration_crudl(client, logged_in_user):
    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)
    integration = Integration.objects.create(
        project=project, kind=Integration.Kind.UPLOAD, name="store_info", ready=True
    )
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    # create -> special flow

    # list
    r = client.get(f"/projects/{project.id}")
    assertOK(r)
    assertLink(r, f"/projects/{project.id}/integrations/", "Integrations")

    r = client.get(f"/projects/{project.id}/integrations/")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(r, INTEGRATION_URL, "store_info")

    # read
    r = client.get(INTEGRATION_URL)
    assertOK(r)
    assertLink(r, f"{INTEGRATION_URL}/settings", "Settings")

    # update
    r = client.get(f"{INTEGRATION_URL}/settings")
    assertOK(r)
    assertFormRenders(r, ["name"])
    assertLink(r, f"{INTEGRATION_URL}/delete", "Delete")

    r = client.post(f"{INTEGRATION_URL}/settings", data={"name": "Store Info"})
    assertRedirects(r, f"{INTEGRATION_URL}/settings", status_code=303)

    integration.refresh_from_db()
    assert integration.name == "Store Info"

    # delete
    r = client.get(f"{INTEGRATION_URL}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"{INTEGRATION_URL}/delete")
    assertRedirects(r, f"/projects/{project.id}/integrations/")

    assert project.integration_set.count() == 0


def test_structure_and_preview(client, logged_in_user, bigquery_client):
    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)
    integration = Integration.objects.create(
        project=project, kind=Integration.Kind.UPLOAD, name="store_info", ready=True
    )
    table = Table.objects.create(
        project=project,
        integration=integration,
        source=Table.Source.INTEGRATION,
        bq_table="table",
        bq_dataset="dataset",
    )
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    r = client.get(INTEGRATION_URL)
    assertOK(r)
    assertLink(r, f"{INTEGRATION_URL}/data", "Data")

    # mock
    # structure, and schema for ibis client
    bq_table = BqTable(
        "project.dataset.table",
        schema=[SchemaField("name", "STRING"), SchemaField("age", "INTEGER")],
    )
    bigquery_client.get_table = MagicMock(return_value=bq_table)

    # structure
    r = client.get_turbo_frame(
        f"{INTEGRATION_URL}/data", f"/integrations/{integration.id}/schema?table_id="
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 2)
    assertContains(r, "name")
    assertContains(r, "Text")

    # preview
    ibis_client().client = bigquery_client
    mock = PickableMock()
    mock.rows_dict = [{"name": "Neera", "age": 4}, {"name": "Vayu", "age": 2}]
    mock.total_rows = 2
    bigquery_client.get_query_results = Mock(return_value=mock)

    r = client.get_turbo_frame(
        f"{INTEGRATION_URL}/data?view=preview",
        f"/integrations/{integration.id}/grid?table_id=",
    )
    assertOK(r)
    print(r.content)
    assertSelectorLength(r, "table tbody tr", 2)

    assertContains(r, "Neera")
    assertContains(r, "4")


def test_create_retry_edit_and_approve(client):
    pass


def test_row_limits(client, logged_in_user):
    pass


def test_pending_cleanup(client, logged_in_user):
    pass
