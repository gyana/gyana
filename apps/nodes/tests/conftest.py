import pytest
from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema


@pytest.fixture
def setup(
    bigquery,
    logged_in_user,
    integration_factory,
    integration_table_factory,
    workflow_factory,
):
    team = logged_in_user.teams.first()
    workflow = workflow_factory(project__team=team)
    integration = integration_factory(project=workflow.project, name="olympia")

    mock_bq_client_with_schema(
        bigquery, [(name, type_.name) for name, type_ in TABLE.schema().items()]
    )
    return (
        integration_table_factory(
            project=workflow.project,
            integration=integration,
        ),
        workflow,
    )
