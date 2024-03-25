import pytest


@pytest.fixture
def setup(
    logged_in_user,
    integration_factory,
    integration_table_factory,
    workflow_factory,
):
    team = logged_in_user.teams.first()
    workflow = workflow_factory(project__team=team)
    integration = integration_factory(project=workflow.project, name="olympia")

    return (
        integration_table_factory(
            project=workflow.project,
            integration=integration,
        ),
        workflow,
    )
