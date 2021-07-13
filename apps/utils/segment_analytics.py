from typing import Final

import analytics
from apps.nodes.models import Node
from apps.users.models import CustomUser

# General
SIGNED_UP_EVENT: Final = "Signed up"
PROJECT_CREATED_EVENT: Final = "Project created"

# Integrations
NEW_INTEGRATION_START_EVENT: Final = "New integration started"
INTEGRATION_CREATED_EVENT: Final = "Integration created"
INTEGRATION_SYNC_SUCCESS_EVENT: Final = "Integration sync succeeded"

# Workflows
WORKFLOW_CREATED_EVENT: Final = "Workflow created"
NODE_CREATED_EVENT: Final = "Node created"
NODE_UPDATED_EVENT: Final = "Node updated"
NODE_CONNECTED_EVENT: Final = "Node connected"
WORFKLOW_RUN_EVENT: Final = "Workflow run"

# Dashboards
DASHBOARD_CREATED_EVENT: Final = "Dashboard created"
WIDGET_CREATED_EVENT: Final = "Widget created"
WIDGET_CONFIGURED_EVENT: Final = "Widget configured"


def identify_user(user: CustomUser):
    analytics.identify(
        user.id,
        {
            "username": user.username,
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            # TODO: add plan information here
        },
    )


def track_node(user: CustomUser, node: Node, track_id: str, **kwargs):
    """Sends tracking event with default fields. Allows for kwargs to be added as additional properties"""
    analytics.track(
        user.id,
        track_id,
        {"id": node.id, "type": node.kind, "workflow_id": node.workflow.id, **kwargs},
    )
