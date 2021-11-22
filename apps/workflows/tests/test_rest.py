import pytest
from django.utils import timezone
from pytest_django.asserts import assertContains

from apps.base.tests.asserts import assertOK
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


def test_workflow_run(
    client,
    project_factory,
    logged_in_user,
    workflow_factory,
    node_factory,
    integration_table_factory,
    bigquery,
):
    """Also tests last_run and out_of_date"""
    mock_bq_client_with_schema(
        bigquery, [(name, type_.name) for name, type_ in TABLE.schema().items()]
    )
    project = project_factory(team=logged_in_user.teams.first())
    workflow = workflow_factory(project=project)

    # check is out_of_date returns out_of_date has not been run
    r = client.get(f"/workflows/{workflow.id}/out_of_date")
    assertOK(r)
    assert r.data["isOutOfDate"]
    assert not r.data["hasBeenRun"]
    output_node = node_factory(
        kind=Node.Kind.OUTPUT, name="The answer", workflow=workflow
    )

    # test running the workflow returns a dictionary with an error
    r = client.post(f"/workflows/{workflow.id}/run_workflow")
    assertOK(r)
    assert r.data == {output_node.id: "node_result_none"}

    input_node = node_factory(
        kind=Node.Kind.INPUT, input_table=integration_table_factory(), workflow=workflow
    )

    output_node._parents.add(input_node)

    with pytest.raises(Node.table.RelatedObjectDoesNotExist):
        output_node.table

    # check last run returns not been run
    r = client.get(f"/workflows/{workflow.id}/last_run")
    assertOK(r)
    assertContains(
        r, "Press the run button after adding some nodes to run this workflow"
    )

    r = client.post(f"/workflows/{workflow.id}/run_workflow")
    assertOK(r)
    output_node.refresh_from_db()
    assert output_node.table

    # check last runs last run
    r = client.get(f"/workflows/{workflow.id}/last_run")
    assertContains(r, "Last run:")

    # check out_of_date is not out_of_date and has been run
    r = client.get(f"/workflows/{workflow.id}/out_of_date")
    assertOK(r)
    assert not r.data["isOutOfDate"]
    assert r.data["hasBeenRun"]

    # fake data update and check is out of date
    # update workflow otherwise changes are overwritten
    workflow.refresh_from_db()
    workflow.data_updated = timezone.now()
    workflow.save()
    r = client.get(f"/workflows/{workflow.id}/out_of_date")
    assertOK(r)
    assert r.data["isOutOfDate"]
    assert r.data["hasBeenRun"]
