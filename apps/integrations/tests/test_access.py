import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertNotFound, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/integrations/{integration_id}/grid", id="grid"),
        pytest.param("/integrations/{integration_id}/schema", id="schema"),
        pytest.param("/projects/{project_id}/integrations/{integration_id}", id="list"),
        pytest.param(
            "/projects/{project_id}/integrations/overview",
            id="overview",
        ),
        pytest.param(
            "/projects/{project_id}/integrations/{integration_id}/configure",
            id="configure",
        ),
        pytest.param(
            "/projects/{project_id}/integrations/{integration_id}/load", id="load"
        ),
        pytest.param(
            "/projects/{project_id}/integrations/{integration_id}/done", id="done"
        ),
        pytest.param(
            "/projects/{project_id}/integrations/{integration_id}", id="detail"
        ),
        pytest.param(
            "/projects/{project_id}/integrations/{integration_id}/delete", id="delete"
        ),
        pytest.param(
            "/projects/{project_id}/integrations/{integration_id}/references",
            id="references",
        ),
        pytest.param(
            "/projects/{project_id}/integrations/{integration_id}/runs", id="runs"
        ),
        pytest.param(
            "/projects/{project_id}/integrations/{integration_id}/settings",
            id="settings",
        ),
    ],
)
def test_integration_access(
    client, url, user, integration_table_factory, upload_factory
):
    integration = integration_table_factory().integration
    upload_factory(integration=integration)

    url = url.format(integration_id=integration.id, project_id=integration.project.id)
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assertNotFound(r)

    integration.project.team = user.teams.first()
    integration.project.save()
    r = client.get(url)
    if "load" in url:
        assert r.status_code == 302
    else:
        assertOK(r)


def test_integration_viewset(client, integration_factory, user):
    integration = integration_factory()

    url = f"/integrations/api/integrations/{integration.id}/"
    r = client.patch(url, data={"name": "Maradona"}, content_type="application/json")
    assert r.status_code == 403

    client.force_login(user)
    r = client.patch(url, data={"name": "Maradona"}, content_type="application/json")
    assertNotFound(r)

    integration.project.team = user.teams.first()
    integration.project.save()
    r = client.patch(url, data={"name": "Maradona"}, content_type="application/json")
    assertOK(r)
