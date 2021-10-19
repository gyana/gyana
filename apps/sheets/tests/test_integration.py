from unittest.mock import Mock

import googleapiclient
import pytest
from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.integrations.models import Integration
from apps.projects.models import Project
from apps.sheets.models import Sheet
from pytest_django.asserts import assertFormError, assertRedirects

pytestmark = pytest.mark.django_db


def test_create(
    client, logged_in_user, bigquery_client, sheets_client, drive_v2_client, settings
):

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)

    # create a new sheet, configure it and complete the sync

    # create
    r = client.get(f"/projects/{project.id}/integrations/sheets/new")
    assertOK(r)
    assertFormRenders(r, ["url"])

    # mock sheet client to get title from Google Sheets
    sheets_client.spreadsheets().get().execute = Mock(
        return_value={"properties": {"title": "Store Info"}}
    )
    r = client.post(
        f"/projects/{project.id}/integrations/sheets/new",
        data={
            "url": "https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit"
        },
    )

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.SHEET
    assert integration.sheet is not None
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    assertRedirects(r, f"{INTEGRATION_URL}/configure", status_code=303)

    # configure
    r = client.get(f"{INTEGRATION_URL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "cell_range"])

    # mock the configuration
    bigquery_client.query().exception = lambda: False
    bigquery_client.reset_mock()  # reset the call count
    bigquery_client.get_table().num_rows = 10

    # mock drive client to check last updated information
    drive_v2_client.files().get().execute = Mock(
        return_value={"modifiedDate": "2020-10-01T00:00:00Z"}
    )

    assert bigquery_client.query.call_count == 0

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(
        f"{INTEGRATION_URL}/configure",
        data={"cell_range": "store_info!A1:D11"},
    )

    assert bigquery_client.query.call_count == 1
    assertRedirects(r, f"{INTEGRATION_URL}/load", target_status_code=302)

    r = client.get(f"{INTEGRATION_URL}/load")
    assertRedirects(r, f"{INTEGRATION_URL}/done")


def test_validation_failures(client, logged_in_user, sheets_client):
    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)

    r = client.get(f"/projects/{project.id}/integrations/sheets/new")
    assertOK(r)
    assertFormRenders(r, ["url"])

    # not a valid url
    r = client.post(
        f"/projects/{project.id}/integrations/sheets/new",
        data={"url": "https://www.google.com"},
    )
    assertFormError(r, "form", "url", "The URL to the sheet seems to be invalid.")

    # not shared with our service account
    def raise_(exc):
        raise exc

    sheets_client.spreadsheets().get().execute = lambda: raise_(
        googleapiclient.errors.HttpError(Mock(), b"")
    )
    r = client.post(
        f"/projects/{project.id}/integrations/sheets/new",
        data={
            "url": "https://docs.google.com/spreadsheets/d/16h15cF3r_7bFjSAeKcy6nnNDpi-CS-NEgUKNCRGXs1E/edit"
        },
    )
    ERROR = "We couldn't access the sheet using the URL provided! Did you give access to the right email?"
    assertFormError(r, "form", "url", ERROR)

    # invalid cell range
    integration = Integration.objects.create(
        project=project, kind=Integration.Kind.SHEET, name="store_info", ready=True
    )
    Sheet.objects.create(
        url="https://docs.google.com/spreadsheets/d/16h15cF3r_7bFjSAeKcy6nnNDpi-CS-NEgUKNCRGXs1E/edit",
        integration=integration,
    )

    r = client.get(f"/projects/{project.id}/integrations/{integration.id}/configure")
    assertOK(r)
    assertFormRenders(r, ["name", "cell_range"])

    error = googleapiclient.errors.HttpError(Mock(), b"")
    error.reason = "Unable to parse range: does_not_exist!A1:D11"
    sheets_client.spreadsheets().get().execute = lambda: raise_(error)

    r = client.post(
        f"/projects/{project.id}/integrations/{integration.id}/configure",
        data={"cell_range": "does_not_exist!A1:D11"},
    )
    assertFormError(
        r, "form", "cell_range", "Unable to parse range: does_not_exist!A1:D11"
    )


def test_runtime_error(client, logged_in_user, bigquery_client, settings):

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)
    integration = Integration.objects.create(
        project=project, kind=Integration.Kind.SHEET, name="store_info"
    )
    Sheet.objects.create(integration=integration, url="http://sheet.url")
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    bigquery_client.query().exception = lambda: True
    bigquery_client.query().errors = [{"message": "No columns found in the schema."}]

    with pytest.raises(Exception):
        r = client.post(
            f"{INTEGRATION_URL}/configure",
            data={"cell_range": "store_info!A20:D21"},
        )

    integration.refresh_from_db()
    assert integration.state == Integration.State.ERROR
