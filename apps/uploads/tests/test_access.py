import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


def test_upload_create(client, user, project_factory):
    project = project_factory()
    url = f"/projects/{project.id}/integrations/uploads/new"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    project.team = user.teams.first()
    project.save()
    r = client.get(url)
    assertOK(r)
