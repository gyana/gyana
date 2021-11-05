import pytest
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.base.tests.mocks import (
    mock_bq_client_with_records,
    mock_bq_client_with_schema,
)
from pytest_django.asserts import assertContains, assertRedirects

pytestmark = pytest.mark.django_db


def test_integration_crudl(client, logged_in_user, sheet_factory):
    team = logged_in_user.teams.first()
    sheet = sheet_factory(integration__project__team=team)
    integration = sheet.integration
    project = integration.project

    LIST = f"/projects/{project.id}/integrations"
    DETAIL = f"{LIST}/{integration.id}"

    # create -> special flow

    # list
    r = client.get(f"/projects/{project.id}")
    assertOK(r)
    assertLink(r, f"{LIST}/", "Integrations")

    r = client.get(f"{LIST}/")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(r, DETAIL, "Store info")

    # read
    r = client.get(DETAIL)
    assertOK(r)
    assertLink(r, f"{DETAIL}/settings", "Settings")

    # update
    r = client.get(f"{DETAIL}/settings")
    assertOK(r)
    assertLink(r, f"{DETAIL}/delete", "Delete")

    r = client.post(f"{DETAIL}/settings", data={"name": "Store Info"})
    assertRedirects(r, f"{DETAIL}/settings", status_code=303)

    integration.refresh_from_db()
    assert integration.name == "Store Info"

    # delete
    r = client.get(f"{DETAIL}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"{DETAIL}/delete")
    assertRedirects(r, f"{LIST}/")

    assert project.integration_set.count() == 0


def test_integration_schema_and_preview(
    client, logged_in_user, bigquery, sheet_factory, integration_table_factory
):
    team = logged_in_user.teams.first()
    sheet = sheet_factory(integration__project__team=team)
    integration = sheet.integration
    project = integration.project
    table = integration_table_factory(project=project, integration=integration)

    # mock table with two columns, 20 rows
    mock_bq_client_with_schema(bigquery, [("name", "STRING"), ("age", "INTEGER")])
    mock_bq_client_with_records(
        bigquery,
        [{"name": "Neera", "age": 4}] * 15 + [{"name": "Vayu", "age": 2}] * 5,
    )

    # test: user can view the data tab, and view the schema and preview information
    # mock the bigquery client and verify it is called with correct args

    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"

    # structure
    r = client.get_turbo_frame(
        f"{DETAIL}?view=schema", f"/integrations/{integration.id}/schema?table_id="
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 2)
    assertContains(r, "name")
    assertContains(r, "Text")

    assert bigquery.get_table.call_count == 1
    assert bigquery.get_table.call_args.args == (table.bq_id,)

    # preview (default)
    r = client.get_turbo_frame(
        f"{DETAIL}",
        f"/integrations/{integration.id}/grid?table_id=",
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 15)
    assertContains(r, "Neera")
    assertContains(r, "4")

    assert bigquery.get_query_results.call_count == 1
    assert bigquery.get_query_results.call_args.args == (
        "SELECT *\nFROM `project.dataset.table`",
    )

    # preview page 2
    assertLink(r, f"/integrations/{integration.id}/grid?table_id=&page=2", "2")

    r = client.get(f"/integrations/{integration.id}/grid?table_id=&page=2")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 20)
    assertContains(r, "Vayu")
    assertContains(r, "2")

    assert bigquery.get_query_results.call_count == 2
    assert bigquery.get_query_results.call_args.args == (
        "SELECT *\nFROM `project.dataset.table`\nLIMIT 5 OFFSET 15",
    )


def test_integration_create_pending_load_and_approve(
    client, logged_in_user, project_factory, sheet_factory, integration_table_factory
):
    team = logged_in_user.teams.first()
    project = project_factory(team=team)

    LIST = f"/projects/{project.id}/integrations"

    # test: zero state, check options to create new integrations, skip to the done step and
    # verify the load redirect and approval workflow

    # zero state
    r = client.get(f"{LIST}/")
    assertOK(r)
    assertContains(r, f"Import a source of data")
    assertLink(r, f"{LIST}/connectors/new", "Add a connector")
    assertLink(r, f"{LIST}/sheets/new", "Add a Google Sheet")
    assertLink(r, f"{LIST}/uploads/new", "Upload CSV")

    sheet = sheet_factory(integration__ready=False, integration__project=project)
    integration = sheet.integration
    integration_table_factory(project=project, integration=integration)

    DETAIL = f"{LIST}/{integration.id}"

    # check that there is an option to create a connector, sheet and upload
    # no zero state
    r = client.get(f"{LIST}/")
    assertOK(r)
    assertContains(r, "New Integration")
    assertLink(r, f"{LIST}/connectors/new", "New Connector")
    assertLink(r, f"{LIST}/sheets/new", "Add Sheet")
    assertLink(r, f"{LIST}/uploads/new", "Upload CSV")

    # the create and configure steps are tested in individual apps
    # the load stage requires celery progress (javascript)
    # we assume that the task was run successfully and is done

    # pending page
    r = client.get(f"{LIST}/pending")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(r, f"{DETAIL}/done", "Store info")

    # load (redirects to done)
    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    # done
    r = client.get(f"{DETAIL}/done")
    assertOK(r)
    assertContains(r, "Review import")
    assertLink(r, f"{DETAIL}", "preview")
    assertLink(r, f"{DETAIL}/configure", "re-configure")
    # todo: fix this!
    assertFormRenders(r, ["name"])

    # confirm and update row count
    assert team.row_count == 0

    r = client.post(f"{DETAIL}/done")
    assertRedirects(r, DETAIL, status_code=303)

    team.refresh_from_db()
    assert team.row_count == 10

    integration.refresh_from_db()
    assert integration.ready

    # ready for done page
    r = client.get(f"{DETAIL}/done")
    assertOK(r)
    assertContains(r, "Success")
    assertLink(r, f"{DETAIL}/configure", "configuration")


def test_integration_exceeds_row_limit(
    client, logged_in_user, sheet_factory, integration_table_factory
):
    team = logged_in_user.teams.first()
    sheet = sheet_factory(integration__ready=False, integration__project__team=team)
    integration = sheet.integration
    project = integration.project
    integration_table_factory(project=project, integration=integration)

    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"
    team.override_row_limit = 5
    team.save()

    # done
    r = client.get(f"{DETAIL}/done")
    assertOK(r)
    assertContains(r, "Insufficient rows")
