import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/workflows/{workflow_id}/duplicate", id="duplicate"),
        # pytest.param("/workflows/{workflow_id}/run_workflow", id="run_workflow"),
        # pytest.param(
        #     "/workflows/{workflow_id}/workflow_out_of_date", id="workflow_out_of_date"
        # ),
        pytest.param("/workflows/{workflow_id}/last_run", id="last_run"),
        pytest.param("/projects/{project_id}/workflows", id="list"),
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
    assert r.status_code == 404

    workflow.project.team = user.teams.first()
    workflow.project.save()
    r = client.get(url)
    assertOK(r)
