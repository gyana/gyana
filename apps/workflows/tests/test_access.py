import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertNotFound, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/workflows/{workflow_id}/duplicate", id="duplicate"),
        pytest.param("/workflows/{workflow_id}/out_of_date", id="workflow_out_of_date"),
        pytest.param("/workflows/{workflow_id}/last_run", id="last_run"),
        pytest.param("/projects/{project_id}/workflows/", id="list"),
        pytest.param("/projects/{project_id}/workflows/overview", id="overview"),
        pytest.param("/projects/{project_id}/workflows/new", id="create"),
        pytest.param("/projects/{project_id}/workflows/{workflow_id}", id="detail"),
        pytest.param(
            "/projects/{project_id}/workflows/{workflow_id}/settings", id="settings"
        ),
        pytest.param(
            "/projects/{project_id}/workflows/{workflow_id}/delete", id="delete"
        ),
    ],
)
def test_workflow_required(client, url, user, workflow_factory):
    workflow = workflow_factory()
    url = url.format(workflow_id=workflow.id, project_id=workflow.project.id)
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assertNotFound(r)

    workflow.project.team = user.teams.first()
    workflow.project.save()
    r = client.get(url)
    assertOK(r)


def test_run_workflow(client, user, workflow_factory):
    workflow = workflow_factory()
    url = f"/workflows/{workflow.id}/run_workflow"
    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.post(url)
    assertNotFound(r)

    workflow.project.team = user.teams.first()
    workflow.project.save()

    r = client.get(url)
    assert r.status_code == 405

    r = client.post(url)
    assertOK(r)


def test_workflow_viewset(client, workflow_factory, user):
    workflow = workflow_factory()

    url = f"/workflows/api/workflows/{workflow.id}/"
    r = client.patch(url, data={"name": "Maradona"}, content_type="application/json")
    assert r.status_code == 403

    client.force_login(user)
    r = client.patch(url, data={"name": "Maradona"}, content_type="application/json")
    assertNotFound(r)

    workflow.project.team = user.teams.first()
    workflow.project.save()
    r = client.patch(url, data={"name": "Maradona"}, content_type="application/json")
    assertOK(r)
