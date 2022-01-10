import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


def test_create_customapi(client, user, project_factory):
    project = project_factory()
    url = f"/projects/{project.id}/integrations/customapis/new"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    project.team = user.teams.first()
    project.save()
    r = client.get(url)
    assertOK(r)
