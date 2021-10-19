import pytest
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.base.tests.mocks import mock_bq_client_with_data, mock_bq_client_with_schema
from apps.integrations.models import Integration
from apps.projects.models import Project
from apps.sheets.models import Sheet
from apps.tables.models import Table
from pytest_django.asserts import assertContains, assertRedirects

pytestmark = pytest.mark.django_db


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
    Table.objects.create(
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

    # mock table with two columns, two rows
    mock_bq_client_with_schema(
        bigquery_client, [("name", "STRING"), ("age", "INTEGER")]
    )
    mock_bq_client_with_data(
        bigquery_client, [{"name": "Neera", "age": 4}, {"name": "Vayu", "age": 2}]
    )

    # structure
    r = client.get_turbo_frame(
        f"{INTEGRATION_URL}/data", f"/integrations/{integration.id}/schema?table_id="
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 2)
    assertContains(r, "name")
    assertContains(r, "Text")

    # preview
    r = client.get_turbo_frame(
        f"{INTEGRATION_URL}/data?view=preview",
        f"/integrations/{integration.id}/grid?table_id=",
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 2)

    assertContains(r, "Neera")
    assertContains(r, "4")


def test_create_retry_edit_and_approve(client, logged_in_user):
    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)

    # check that there is an option to create a connector, sheet and upload
    r = client.get(f"/projects/{project.id}/integrations/")
    assertOK(r)
    assertContains(r, "New Integration")
    assertLink(
        r, f"/projects/{project.id}/integrations/connectors/new", "New Connector"
    )
    assertLink(r, f"/projects/{project.id}/integrations/sheets/new", "Add Sheet")
    assertLink(r, f"/projects/{project.id}/integrations/uploads/new", "Upload CSV")

    # the create and configure steps are tested in individual apps
    # the load stage requires celery progress (javascript)
    # we assume that the task was run successfully and is done

    integration = Integration.objects.create(
        project=project,
        kind=Integration.Kind.SHEET,
        name="store_info",
        state=Integration.State.DONE,
    )
    Sheet.objects.create(integration=integration, url="http://sheet.url")
    Table.objects.create(
        bq_table="table",
        bq_dataset="dataset",
        project=project,
        source=Table.Source.INTEGRATION,
        integration=integration,
        num_rows=10,
    )
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    # pending page
    r = client.get(f"/projects/{project.id}/integrations/pending")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(r, INTEGRATION_URL, "store_info")

    # redirect from detail page
    r = client.get(INTEGRATION_URL)
    assertRedirects(r, f"{INTEGRATION_URL}/done")

    # load (redirects to done)
    r = client.get(f"{INTEGRATION_URL}/load")
    assertRedirects(r, f"{INTEGRATION_URL}/done")

    # done
    r = client.get(f"{INTEGRATION_URL}/done")
    assertOK(r)
    assertContains(r, "Review import")
    assertLink(r, f"{INTEGRATION_URL}/data", "preview")
    assertLink(r, f"{INTEGRATION_URL}/configure", "re-configure")
    # todo: fix this!
    assertFormRenders(r, ["name"])

    # confirm and update row count
    assert team.row_count == 0

    r = client.post(f"{INTEGRATION_URL}/done")
    assertRedirects(r, INTEGRATION_URL, status_code=303)

    team.refresh_from_db()
    assert team.row_count == 10

    integration.refresh_from_db()
    assert integration.ready

    # ready for done page
    r = client.get(f"{INTEGRATION_URL}/done")
    assertOK(r)
    assertContains(r, "Success")
    assertLink(r, f"{INTEGRATION_URL}/configure", "configuration")


def test_exceeds_row_limit(client, logged_in_user):
    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)
    integration = Integration.objects.create(
        project=project,
        kind=Integration.Kind.SHEET,
        name="store_info",
        state=Integration.State.DONE,
    )
    Table.objects.create(
        bq_table="table",
        bq_dataset="dataset",
        project=project,
        source=Table.Source.INTEGRATION,
        integration=integration,
        num_rows=10,
    )
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    team.override_row_limit = 5
    team.save()

    # done
    r = client.get(f"{INTEGRATION_URL}/done")
    assertOK(r)
    assertContains(r, "Insufficient rows")
