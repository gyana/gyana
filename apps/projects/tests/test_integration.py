import pytest
from deepdiff import DeepDiff
from pytest_django.asserts import assertContains, assertRedirects

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorHasAttribute,
    assertSelectorLength,
)
from apps.base.tests.snapshot import get_instance_dict
from apps.nodes.models import Node
from apps.projects.models import Project
from apps.tables.models import Table
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db(transaction=True)


def test_project_crudl(client, logged_in_user):
    team = logged_in_user.teams.first()

    # create
    r = client.get(f"/teams/{team.id}")
    # zero state link
    assertLink(r, f"/teams/{team.id}/projects/new", "Create a new project")

    r = client.get(f"/teams/{team.id}/projects/new")
    assertOK(r)
    assertFormRenders(r, ["name", "description", "access", "members"])

    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "description": "All the company metrics",
            "access": "everyone",
        },
    )
    project = team.project_set.first()
    assert project is not None
    assertRedirects(r, f"/projects/{project.id}", status_code=303)

    # read
    r = client.get(f"/projects/{project.id}")
    assertOK(r)
    assertContains(r, "Metrics")
    assertContains(r, "All the company metrics")
    assertLink(r, f"/projects/{project.id}/update", "Settings")

    # list
    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertLink(r, f"/projects/{project.id}", "Metrics")
    # normal link
    assertLink(r, f"/teams/{team.id}/projects/new", "New Project")

    # update
    r = client.get(f"/projects/{project.id}/update")
    assertOK(r)
    assertFormRenders(r, ["name", "description", "access", "members"])
    assertLink(r, f"/projects/{project.id}/delete", "Delete")

    r = client.post(
        f"/projects/{project.id}/update",
        data={
            "name": "KPIs",
            "description": "All the company kpis",
            "access": "everyone",
        },
    )
    assertRedirects(r, f"/projects/{project.id}/update", status_code=303)

    project.refresh_from_db()
    assert project.name == "KPIs"

    # delete
    r = client.get(f"/projects/{project.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/projects/{project.id}/delete")
    assertRedirects(r, f"/teams/{team.id}")

    assert team.project_set.first() is None


def test_private_projects(client, logged_in_user):
    team = logged_in_user.teams.first()

    other_user = CustomUser.objects.create_user("other user")
    team.members.add(other_user, through_defaults={"role": "admin"})

    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "description": "All the company metrics",
            "access": "invite",
            "members": [logged_in_user.id],
        },
    )

    project = team.project_set.first()
    assert project is not None

    # validate access
    assertOK(client.get(f"/projects/{project.id}"))

    # validate forbidden
    client.force_login(other_user)
    assertSelectorLength(client.get(f"/teams/{team.id}"), "table tbody tr", 0)
    assert client.get(f"/projects/{project.id}").status_code == 404


def test_automate(client, logged_in_user, project_factory, graph_run_factory):
    team = logged_in_user.teams.first()
    project = project_factory(team=team)
    graph_run_factory.create_batch(3, project=project)

    r = client.get(f"/projects/{project.id}/automate")
    assertOK(r)

    r = client.get(f"/projects/{project.id}/runs")
    assertOK(r)
    assertFormRenders(r, ["daily_schedule_time"])
    assertSelectorLength(r, "table tbody tr", 3)

    r = client.post(
        f"/projects/{project.id}/runs", data={"daily_schedule_time": "06:00"}
    )
    assertRedirects(r, f"/projects/{project.id}/runs", status_code=303)

    project.refresh_from_db()

    assert project.daily_schedule_time.hour == 6


def test_duplicate_simple_project(
    client,
    engine,
    project,
    integration_factory,
    upload_factory,
    node_factory,
    widget_factory,
):
    """Tests duplication of a project with an upload integration,
    a workflow with an input node to that integration's table and an output node,
    with a table,
    a dashboard with a widget depending on that output node table.

    Confirms dependencies are updated correctly and deletion doesnt change the
    original project."""
    # Create integration
    integration = integration_factory(project=project, kind="upload")
    upload = upload_factory(integration=integration)
    table = integration.table_set.create(
        namespace="project.dataset",
        name=upload.table_id,
        project=project,
        source=Table.Source.INTEGRATION,
    )

    # Create workflow
    input_node = node_factory(workflow__project=project, input_table=table)
    output_node = node_factory(workflow=input_node.workflow, kind="output")
    output_node.parents.add(input_node)
    output_table = Table(
        workflow_node=output_node,
        source=Table.Source.WORKFLOW_NODE,
        namespace="project.dataset",
        project=project,
        name=output_node.bq_output_table_id,
    )
    output_table.save()

    # Create dashboard
    widget_factory(page__dashboard__project=project, kind="table", table=output_table)
    project_dict = get_instance_dict(project)

    r = client.post(f"/projects/{project.id}/duplicate")
    assert r.status_code == 303
    duplicate = Project.objects.exclude(id=project.id).first()

    assert duplicate.name == f"Copy of {project.name}"
    assert duplicate.integration_set.count() == 1
    assert duplicate.workflow_set.count() == 1
    assert duplicate.dashboard_set.count() == 1
    assert duplicate.table_set.count() == 2
    assert duplicate.workflow_set.first().nodes.count() == 2
    assert duplicate.dashboard_set.first().pages.first().widgets.count() == 1

    duplicate_table = duplicate.integration_set.first().table_set.first()
    assert duplicate_table.namespace == table.namespace
    assert duplicate_table.name == duplicate_table.integration.upload.table_id

    # Test dependencies have been replaced correctly
    duplicate_nodes = Node.objects.filter(workflow__project=duplicate)
    duplicate_input_node = duplicate_nodes.filter(kind=Node.Kind.INPUT).first()
    duplicate_output_node = duplicate_nodes.filter(kind=Node.Kind.OUTPUT).first()
    assert duplicate_input_node.input_table == duplicate_table
    assert duplicate_output_node.parents.first() == duplicate_input_node

    duplicate_widget = duplicate.dashboard_set.first().pages.first().widgets.first()
    assert duplicate_widget.table == duplicate_output_node.table

    # Check the two tables from integration and workflow have been copied in bigquery
    assert engine.raw_sql.call_count == 2
    call_queries = [arg.args[0] for arg in engine.raw_sql.call_args_list]
    assert (
        f"CREATE OR REPLACE TABLE {duplicate_table.fqn} as (SELECT * FROM {table.fqn})"
        in call_queries
    )
    assert (
        f"CREATE OR REPLACE TABLE {duplicate_output_node.table.fqn} as (SELECT * FROM {output_node.table.fqn})"
        in call_queries
    )

    r = client.delete(f"/projects/{duplicate.id}/delete")
    assert r.status_code == 302

    new_project_dict = get_instance_dict(project)
    # Confirm original project hasn't been changed through deletion
    assert not DeepDiff(project_dict, new_project_dict)
