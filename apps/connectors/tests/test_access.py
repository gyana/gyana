import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK
from apps.connectors.tests.mock import get_mock_fivetran_connector
from apps.projects.models import Project

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/connectors/{}/icon", id="icon"),
        pytest.param("/connectors/{}/status", id="status"),
    ],
)
def test_connector_required(client, url, user, connector_factory, fivetran):
    fivetran.get.return_value = get_mock_fivetran_connector()
    connector = connector_factory()
    assertLoginRedirect(client, url.format(connector.id))

    client.force_login(user)
    r = client.get(url.format(connector.id))
    assert r.status_code == 404

    team_connector = connector_factory(integration__project__team=user.teams.first())
    r = client.get(url.format(team_connector.id))
    assertOK(r)


@pytest.mark.parametrize(
    "url, success_code",
    [
        pytest.param("/projects/{}/integrations/connectors/new", 200, id="new"),
        pytest.param(
            "/projects/{}/integrations/connectors/{}/authorize", 302, id="authorize"
        ),
    ],
)
def test_project_required(
    client, url, success_code, user, project_factory, connector_factory
):
    project = project_factory()
    connector = connector_factory(integration__project=project)
    no_login_url = url.format(
        *([project.id, connector.id] if url.count("{}") == 2 else [project.id])
    )
    assertLoginRedirect(client, no_login_url)

    client.force_login(user)
    r = client.get(no_login_url)
    assert r.status_code == 404

    team_project = project_factory(team=user.teams.first())
    team_connector = connector_factory(integration__project=team_project)

    team_url = url.format(
        *(
            [team_project.id, team_connector.id]
            if url.count("{}") == 2
            else [team_project.id]
        )
    )
    r = client.get(team_url)
    assert r.status_code == success_code

    team_project.access = Project.Access.INVITE_ONLY
    team_project.save()
    r = client.get(team_url)
    assert r.status_code == 404

    team_project.members.add(user)
    r = client.get(team_url)
    assert r.status_code == success_code
