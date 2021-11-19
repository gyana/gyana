import pytest
from pytest_django.asserts import assertContains, assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK

pytestmark = pytest.mark.django_db


def test_workflow_crudl(client, project_factory, logged_in_user, workflow_factory):
    project = project_factory(team=logged_in_user.teams.first())
    project_url = f"/projects/{project.id}"

    # zero state
    r = client.get(f"{project_url}/workflows/")
    assertOK(r)
    assertFormRenders(r, ["project"])
    assertContains(r, "Create a new workflow")

    # create
    r = client.post(f"{project_url}/workflows/new", data={"project": project.id})
    workflow = project.workflow_set.first()
    assert workflow is not None
    assertRedirects(r, f"{project_url}/workflows/{workflow.id}", status_code=303)

    # read
    r = client.get(f"{project_url}/workflows/{workflow.id}")
    assertOK(r)
    assertFormRenders(r, ["name"])

    # update/rename
    new_name = "Superduper workflow"
    r = client.post(f"{project_url}/workflows/{workflow.id}", data={"name": new_name})
    assertRedirects(r, f"{project_url}/workflows/{workflow.id}", status_code=303)
    workflow.refresh_from_db()
    assert workflow.name == new_name

    # delete
    r = client.get(f"{project_url}/workflows/{workflow.id}/delete")
    assertOK(r)
    assertFormRenders(r)
    r = client.delete(f"{project_url}/workflows/{workflow.id}/delete")
    assertRedirects(r, f"{project_url}/workflows/")
    assert project.workflow_set.first() is None

    # list with pagination
    workflow_factory.create_batch(30, project=project)
    r = client.get(f"{project_url}/workflows/")
    assertOK(r)
    assertLink(r, f"{project_url}/workflows/?page=2", "2")
    r = client.get(f"{project_url}/workflows/?page=2")
    assertOK(r)
