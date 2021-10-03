from unittest.mock import Mock

import googleapiclient
import pytest
from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.integrations.models import Integration
from apps.projects.models import Project
from apps.sheets.models import Sheet
from pytest_django.asserts import assertFormError

pytestmark = pytest.mark.django_db


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
