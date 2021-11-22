from datetime import datetime
from unittest.mock import Mock, patch

import googleapiclient
import pytest
from django.core import mail
from pytest_django.asserts import assertContains, assertFormError, assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.integrations.models import Integration

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def bq_table_schema_is_not_string_only(mocker):
    mocker.patch(
        "apps.sheets.bigquery.bq_table_schema_is_string_only", return_value=False
    )


def test_sheet_create(
    client,
    logged_in_user,
    project,
    bigquery,
    sheets,
    drive_v2,
):

    # mock sheet client to get title from Google Sheets
    sheets.spreadsheets().get().execute = Mock(
        return_value={"properties": {"title": "Store Info"}}
    )
    # mock the configuration
    bigquery.query().exception = lambda: False
    bigquery.reset_mock()
    # mock drive client to check last updated information
    drive_v2.files().get().execute = Mock(
        return_value={"modifiedDate": "2020-10-01T00:00:00Z"}
    )

    LIST = f"/projects/{project.id}/integrations"
    SHEETS_URL = "https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit"
    CELL_RANGE = "store_info!A1:D11"

    # test: create a new sheet, configure it and complete the sync

    # create
    r = client.get(f"{LIST}/sheets/new")
    assertOK(r)
    assertFormRenders(r, ["url"])

    r = client.post(f"{LIST}/sheets/new", data={"url": SHEETS_URL})

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.SHEET
    assert integration.sheet is not None
    assert integration.created_by == logged_in_user
    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"

    assertRedirects(r, f"{DETAIL}/configure", status_code=303)

    # configure
    r = client.get(f"{DETAIL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "cell_range"])

    assert bigquery.query.call_count == 0

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(f"{DETAIL}/configure", data={"cell_range": CELL_RANGE})

    assert bigquery.query.call_count == 1

    # validate the sql and external table configuration
    table = integration.table_set.first()
    SQL = f"CREATE OR REPLACE TABLE {table.bq_id} AS SELECT * FROM {table.bq_table}_external"
    assert bigquery.query.call_args.args == (SQL,)
    job_config = bigquery.query.call_args.kwargs["job_config"]
    external_config = job_config.table_definitions[f"{table.bq_table}_external"]
    assert external_config.source_uris == [SHEETS_URL]
    assert external_config.autodetect
    assert external_config.options.range == CELL_RANGE

    assertRedirects(r, f"{DETAIL}/load", target_status_code=302)

    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    # todo: email
    # assert len(mail.outbox) == 1


def test_validation_failures(client, logged_in_user, sheet_factory, sheets):
    team = logged_in_user.teams.first()
    SHEET_URL = "https://docs.google.com/spreadsheets/d/16h15cF3r_7bFjSAeKcy6nnNDpi-CS-NEgUKNCRGXs1E/edit"
    sheet = sheet_factory(url=SHEET_URL, integration__project__team=team)

    LIST = f"/projects/{sheet.integration.project.id}/integrations"
    DETAIL = f"{LIST}/{sheet.integration.id}"

    # test: validation failures when submitting initial url and cell range

    r = client.get(f"{LIST}/sheets/new")
    assertOK(r)
    assertFormRenders(r, ["url"])

    # not a valid url
    r = client.post(f"{LIST}/sheets/new", data={"url": "https://www.google.com"})
    assertFormError(r, "form", "url", "The URL to the sheet seems to be invalid.")

    # not shared with our service account
    def raise_(exc):
        raise exc

    sheets.spreadsheets().get().execute = lambda: raise_(
        googleapiclient.errors.HttpError(Mock(), b"")
    )
    r = client.post(f"{LIST}/sheets/new", data={"url": SHEET_URL})
    ERROR = "We couldn't access the sheet using the URL provided! Did you give access to the right email?"
    assertFormError(r, "form", "url", ERROR)

    # invalid cell range
    r = client.get(f"{DETAIL}/configure")
    assertOK(r)
    assertFormRenders(r, ["name", "cell_range"])

    error = googleapiclient.errors.HttpError(Mock(), b"")
    error.reason = "Unable to parse range: does_not_exist!A1:D11"
    sheets.spreadsheets().get().execute = lambda: raise_(error)

    r = client.post(f"{DETAIL}/configure", data={"cell_range": "does_not_exist!A1:D11"})
    assertFormError(r, "form", "cell_range", error.reason)


def test_runtime_error(client, logged_in_user, sheet_factory, bigquery):

    team = logged_in_user.teams.first()
    sheet = sheet_factory(integration__project__team=team)
    integration = sheet.integration

    DETAIL = f"/projects/{integration.project.id}/integrations/{integration.id}"

    # test: runtime errors lead to error state

    bigquery.query().exception = lambda: True
    bigquery.query().errors = [{"message": "No columns found in the schema."}]

    with pytest.raises(Exception):
        client.post(
            f"{DETAIL}/configure",
            data={"cell_range": "store_info!A20:D21"},
        )

    integration.refresh_from_db()
    assert integration.state == Integration.State.ERROR
    assert integration.table_set.count() == 0


def test_resync_after_source_update(
    client, logged_in_user, sheet_factory, drive_v2, bigquery
):

    team = logged_in_user.teams.first()
    sheet = sheet_factory(
        integration__project__team=team,
        drive_file_last_modified_at_sync=datetime(2020, 9, 1, 0, 0, 0),
    )
    integration = sheet.integration
    # mock drive client to check last updated information
    drive_v2.files().get().execute = Mock(
        return_value={"modifiedDate": "2020-10-01T00:00:00Z"}
    )
    bigquery.query().exception = lambda: False
    bigquery.reset_mock()  # reset the call count

    DETAIL = f"/projects/{integration.project.id}/integrations/{integration.id}"

    # test: an outdated sheet information is displayed, and can be updated

    # sheet is out of date
    r = client.get_turbo_frame(f"{DETAIL}", f"/sheets/{sheet.id}/status")
    assertOK(r)
    assertContains(r, "sync the latest data")
    assertLink(r, f"{DETAIL}/configure", "sync the latest data")

    r = client.get(f"{DETAIL}/configure")
    assertOK(r)

    # sync new data
    r = client.post(f"{DETAIL}/configure")

    # sheet is up to date
    r = client.get_turbo_frame(f"{DETAIL}", f"/sheets/{sheet.id}/status")
    assertOK(r)
    assertContains(r, "up to date")

    # no email
    assert len(mail.outbox) == 0
