from datetime import datetime
from unittest.mock import Mock

import googleapiclient
import pytest
from celery import states
from django.core import mail
from pytest_django.asserts import assertFormError, assertNotContains, assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.integrations.models import Integration

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def bq_table_schema_is_not_string_only(mocker):
    mocker.patch(
        "apps.base.engine.bigquery.bq_table_schema_is_string_only", return_value=False
    )


def test_sheet_create(
    client,
    logged_in_user,
    project,
    engine,
    sheets,
    drive_v2,
):
    # mock sheet client to get title from Google Sheets
    sheets.spreadsheets().get().execute = Mock(
        return_value={"properties": {"title": "Store Info"}}
    )
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
    # Configuration shows up at the same page now
    assertFormRenders(r, ["url", "is_scheduled", "cell_range", "sheet_name"])

    r = client.post(
        f"{LIST}/sheets/new",
        data={
            "url": SHEETS_URL,
            "sheet_name": "",
            "cell_range": "",
            "is_scheduled": True,
        },
    )

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.SHEET
    assert integration.sheet is not None
    assert integration.created_by == logged_in_user
    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"

    assertRedirects(r, f"{DETAIL}/load", status_code=303, target_status_code=302)

    # Task should have ran already
    assert integration.runs.count() == 1

    # Import should have happened already
    assert engine.query.call_count == 1

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(
        f"{DETAIL}/configure",
        data={
            "sheet_name": "",
            "cell_range": CELL_RANGE,
            "is_scheduled": False,
        },
    )

    # validate the sql and external table configuration
    table = integration.table_set.first()
    SQL = f"CREATE OR REPLACE TABLE {table.fqn} AS SELECT * FROM {table.name}_external"
    assert engine.query.call_args.args == (SQL,)
    job_config = engine.query.call_args.kwargs["job_config"]
    external_config = job_config.table_definitions[f"{table.name}_external"]
    assert external_config.source_uris == [SHEETS_URL]
    assert external_config.autodetect
    assert external_config.options.range == CELL_RANGE

    assertRedirects(r, f"{DETAIL}/load", target_status_code=302)

    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    # validate the run and task result exist, both times
    assert integration.runs.count() == 2
    run = integration.runs.first()
    assert run.result is not None
    assert run.result.status == states.SUCCESS

    assert len(mail.outbox) == 1


def test_validation_failures(client, logged_in_user, sheet_factory, sheets):
    team = logged_in_user.teams.first()
    SHEET_URL = "https://docs.google.com/spreadsheets/d/16h15cF3r_7bFjSAeKcy6nnNDpi-CS-NEgUKNCRGXs1E/edit"
    sheet = sheet_factory(url=SHEET_URL, integration__project__team=team)

    LIST = f"/projects/{sheet.integration.project.id}/integrations"
    DETAIL = f"{LIST}/{sheet.integration.id}"

    # test: validation failures when submitting initial url and cell range

    r = client.get(f"{LIST}/sheets/new")
    assertOK(r)
    assertFormRenders(r, ["is_scheduled", "url", "cell_range", "sheet_name"])

    # not a valid url
    r = client.post(
        f"{LIST}/sheets/new",
        data={
            "url": "https://www.google.com",
            "sheet_name": "",
            "cell_range": "",
            "is_scheduled": True,
        },
    )
    assertFormError(r, "form", "url", "The URL to the sheet seems to be invalid.")

    # not shared with our service account
    def raise_(exc):
        raise exc

    sheets.spreadsheets().get().execute = lambda: raise_(
        googleapiclient.errors.HttpError(Mock(), b"")
    )
    r = client.post(
        f"{LIST}/sheets/new",
        data={
            "url": SHEET_URL,
            "sheet_name": "",
            "cell_range": "",
            "is_scheduled": True,
        },
    )
    ERROR = "We couldn't access the sheet using the URL provided! Did you give access to the right email?"
    assertFormError(r, "form", "url", ERROR)

    # invalid cell range
    r = client.get(f"{DETAIL}/configure")
    assertOK(r)
    assertFormRenders(
        r, ["sheet_name", "cell_range", "is_scheduled"], "#configure-update-form"
    )

    error = googleapiclient.errors.HttpError(Mock(), b"")
    error.reason = "Unable to parse range: does_not_exist!A1:D11"
    sheets.spreadsheets().get().execute = lambda: raise_(error)

    r = client.post(
        f"{DETAIL}/configure",
        data={"sheet_name": "", "cell_range": "does_not_exist!A1:D11"},
    )
    assertFormError(r, "form", "cell_range", error.reason)


def test_runtime_error(client, logged_in_user, sheet_factory, engine, drive_v2):
    team = logged_in_user.teams.first()
    sheet = sheet_factory(integration__project__team=team)
    integration = sheet.integration
    drive_v2.files().get().execute = Mock(
        return_value={"modifiedDate": "2020-10-01T00:00:00Z"}
    )

    DETAIL = f"/projects/{integration.project.id}/integrations/{integration.id}"

    # test: runtime errors lead to error state

    engine.query.return_value.exception.return_value = True
    engine.query.return_value.errors = [{"message": "No columns found in the schema."}]

    # celery eager mode does not store error results in the backend, but it is enough
    # to check an exception happens

    with pytest.raises(Exception):
        client.post(
            f"{DETAIL}/configure",
            data={
                "sheet_name": "",
                "cell_range": "store_info!A20:D21",
                "is_scheduled": False,
            },
        )

    assert sheet.integration.runs.count() == 1


def test_resync_after_source_update(
    client, logged_in_user, sheet_factory, drive_v2, engine
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
    engine.query.exception = lambda timeout: False

    DETAIL = f"/projects/{integration.project.id}/integrations/{integration.id}"

    # test: an outdated sheet information is displayed, and can be updated

    # sheet is out of date
    r = client.get_htmx_partial(f"{DETAIL}", f"/sheets/{sheet.id}/status")
    assertOK(r)

    r = client.get(f"{DETAIL}/configure")
    assertOK(r)

    # sync new data
    r = client.post(f"{DETAIL}/sync")

    # sheet is up to date
    r = client.get_htmx_partial(f"{DETAIL}", f"/sheets/{sheet.id}/status")
    assertOK(r)
    assertNotContains(r, "sync the latest data")

    # no email
    assert len(mail.outbox) == 0
