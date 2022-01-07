from unittest.mock import Mock

import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


def test_sheet_status(client, user, drive_v2, sheet_factory):
    sheet = sheet_factory()
    drive_v2.files().get().execute = Mock(
        return_value={"modifiedDate": "2020-10-01T00:00:00Z"}
    )
    url = f"/sheets/{sheet.id}/status"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    sheet.integration.project.team = user.teams.first()
    sheet.integration.project.save()
    r = client.get(url)
    assertOK(r)


def test_sheet_create(client, user, project_factory):
    project = project_factory()
    url = f"/projects/{project.id}/integrations/sheets/new"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    project.team = user.teams.first()
    project.save()
    r = client.get(url)
    assertOK(r)
