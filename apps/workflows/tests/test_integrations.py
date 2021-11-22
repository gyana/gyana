import pytest
from django.db.models import Q
from pytest_django.asserts import assertContains, assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.nodes.models import Node
from apps.workflows.models import Workflow

pytestmark = pytest.mark.django_db


def test_workflow_crudl(client, project, workflow_factory):
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


def test_workflow_duplication(client, project, workflow_factory, node_factory):
    name = "What is the universe?"
    workflow = workflow_factory(project=project, name=name)

    input_1, input_2 = node_factory.create_batch(
        2, kind=Node.Kind.INPUT, workflow=workflow
    )
    join_node = node_factory(kind=Node.Kind.JOIN, workflow=workflow)
    # Hard code position in reverse addition order
    join_node.parents.add(input_1, through_defaults={"position": 1})
    join_node.parents.add(input_2, through_defaults={"position": 0})

    r = client.post(f"/workflows/{workflow.id}/duplicate")
    assertRedirects(r, f"/projects/{project.id}/workflows/", status_code=303)

    assert Workflow.objects.count() == 2
    assert Node.objects.count() == 6

    new_workflow = Workflow.objects.filter(~Q(id=workflow.id)).first()
    assert new_workflow.name == f"Copy of {name}"
    assert new_workflow.last_run is None

    new_input_1, new_input_2 = new_workflow.nodes.filter(kind=Node.Kind.INPUT).all()
    new_join_node = new_workflow.nodes.filter(kind=Node.Kind.JOIN).first()

    assert {p.id for p in new_join_node.parents.all()} == {
        new_input_1.id,
        new_input_2.id,
    }
    assert new_input_1.child_set.first().position == 1
    assert new_input_2.child_set.first().position == 0
