import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/projects/{}", id="id"),
        pytest.param("/projects/{}/update", id="update"),
        pytest.param("/projects/{}/delete", id="delete"),
        pytest.param("/projects/{}/automate", id="automate"),
        pytest.param("/projects/{}/runs", id="runs"),
        pytest.param("/projects/{}/duplicate", id="duplicate"),
    ],
)
def test_project_required(client, url, user, project_factory):
    project = project_factory()
    url = url.format(project.id)
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    project.team = user.teams.first()
    project.save()
    r = client.get(url)
    assertOK(r)


def test_project_run(client, user, project_factory):
    project = project_factory()
    url = f"/projects/{project.id}/run"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.post(url)
    assert r.status_code == 404

    project.team = user.teams.first()
    project.save()

    r = client.get(url)
    assert r.status_code == 405

    r = client.post(url)
    assertOK(r)


def test_project_create(client, user, team_factory):
    team = team_factory()
    url = f"/teams/{team.id}/projects/new"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assert r.status_code == 404

    team.members.add(user)
    r = client.get(url)
    assertOK(r)
