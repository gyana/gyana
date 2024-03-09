import hashlib

import pandas as pd
import pytest
from ibis.backends.bigquery import Backend
from pytest_django.asserts import assertContains, assertRedirects

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)

pytestmark = pytest.mark.django_db


def md5(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()


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
    assertFormRenders(r, ["name"], "#integrations-name")
    assertLink(r, f"{DETAIL}/settings", "Settings")

    # name
    new_name = "Superduper integration"
    r = client.post(f"/integrations/{integration.id}/name", data={"name": new_name})
    assertRedirects(r, f"/integrations/{integration.id}/name", status_code=303)
    integration.refresh_from_db()
    assert integration.name == new_name

    # update
    r = client.get(f"{DETAIL}/settings")
    assertOK(r)
    assertLink(r, f"{DETAIL}/delete", "Delete")

    # delete
    r = client.get(f"{DETAIL}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"{DETAIL}/delete")
    assertRedirects(r, f"{LIST}/")

    assert project.integration_set.count() == 0


def test_integration_schema_and_preview(
    client,
    logged_in_user,
    mocker,
    mock_bigquery,
    sheet_factory,
    integration_table_factory,
):
    bq_execute = mocker.patch.object(Backend, "execute", return_value=pd.DataFrame())
    team = logged_in_user.teams.first()
    sheet = sheet_factory(integration__project__team=team)
    integration = sheet.integration
    project = integration.project
    integration_table_factory(project=project, integration=integration)

    # mock table with two columns, 20 rows

    # test: user can view the data tab, and view the schema and preview information
    # mock the bigquery client and verify it is called with correct args

    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"

    # structure
    r = client.get_htmx_partial(
        f"{DETAIL}?view=schema", f"/integrations/{integration.id}/schema?table_id="
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 9)
    assertContains(r, "name")
    assertContains(r, "Text")

    # preview (default)
    r = client.get_htmx_partial(
        f"{DETAIL}",
        f"/integrations/{integration.id}/grid?table_id=",
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 15)
    assertContains(r, "Neera")
    assertContains(r, "4")

    assert bq_execute.call_count == 1
    assert bq_execute.call_args.args == (
        "SELECT t0.*\nFROM `project.dataset.table` t0",
    )

    # preview page 2
    assertLink(
        r, f"/integrations/{integration.id}/grid?table_id=&page=2", "2", htmx=True
    )

    r = client.get(f"/integrations/{integration.id}/grid?table_id=&page=2")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 20)
    assertContains(r, "Vayu")
    assertContains(r, "2")

    assert bq_execute.call_count == 2
    assert bq_execute.call_args.args == (
        "SELECT t0.*\nFROM `project.dataset.table` t0\nLIMIT 5 OFFSET 15",
    )

    # preview page 2 with sort
    SORT_URL = (
        f"/integrations/{integration.id}/grid?table_id=&page=2&sort={md5('name')}"
    )
    assertLink(r, SORT_URL, htmx=True)

    r = client.get(SORT_URL)
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 20)
    assertContains(r, "Vayu")
    assertContains(r, "2")

    assert bq_execute.call_count == 3
    assert bq_execute.call_args.args == (
        "SELECT t0.*\nFROM `project.dataset.table` t0\nORDER BY t0.`name` DESC\nLIMIT 5 OFFSET 15",
    )


def test_integration_create_pending_load_and_approve(
    client, logged_in_user, project, sheet_factory, integration_table_factory
):
    team = logged_in_user.teams.first()

    LIST = f"/projects/{project.id}/integrations"

    # test: zero state, check options to create new integrations, skip to the done step and
    # verify the load redirect and approval workflow

    # zero state
    r = client.get(f"{LIST}/")
    assertOK(r)
    assertContains(r, "Import a source of data")
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
    assertLink(r, f"{LIST}/sheets/new", "Add Sheet")
    assertLink(r, f"{LIST}/uploads/new")

    # the create and configure steps are tested in individual apps
    # the load stage requires celery progress (javascript)
    # we assume that the task was run successfully and is done

    # load (redirects to done)
    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    # done
    r = client.get(f"{DETAIL}/done")
    assertOK(r)
    assertContains(r, "Review import")
    assertLink(r, f"{DETAIL}/configure", "Reconfigure")
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

    # view list of runs
    r = client.get(f"{DETAIL}/runs")
    assertOK(r)
