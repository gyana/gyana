from typing import Final

from apps.nodes.models import Node
from apps.users.models import CustomUser

import analytics

# users
SIGNED_UP_EVENT: Final = "Signed up"
ONBOARDING_COMPLETED_EVENT: Final = "Onboarding completed"
APPSUMO_CODE_REDEEMED_EVENT: Final = "AppSumo code redeemed"

# teams
TEAM_CREATED_EVENT: Final = "Team created"
INVITE_SENT_EVENT: Final = "Invite sent"
INVITE_ACCEPTED_EVENT: Final = "Invite accepted"

# projects
PROJECT_CREATED_EVENT: Final = "Project created"

# templates
TEMPLATE_VIEWED_EVENT: Final = "Template viewed"
TEMPLATE_CREATED_EVENT: Final = "Template created"
TEMPLATE_COMPLETED_EVENT: Final = "Template completed"

# integrations
NEW_INTEGRATION_START_EVENT: Final = "New integration started"
INTEGRATION_CREATED_EVENT: Final = "Integration created"
INTEGRATION_SYNC_SUCCESS_EVENT: Final = "Integration sync succeeded"

# workflows
WORKFLOW_CREATED_EVENT: Final = "Workflow created"
WORKFLOW_DUPLICATED_EVENT: Final = "Workflow duplicated"
NODE_CREATED_EVENT: Final = "Node created"
NODE_UPDATED_EVENT: Final = "Node updated"
NODE_CONNECTED_EVENT: Final = "Node connected"
WORFKLOW_RUN_EVENT: Final = "Workflow run"

# dashboards
DASHBOARD_CREATED_EVENT: Final = "Dashboard created"
DASHBOARD_DUPLICATED_EVENT: Final = "Dashboard duplicated"
WIDGET_CREATED_EVENT: Final = "Widget created"
WIDGET_DUPLICATED_EVENT: Final = "Widget duplicated"
WIDGET_CONFIGURED_EVENT: Final = "Widget configured"
DASHBOARD_SHARED_PUBLIC_EVENT: Final = "Dashboard shared public"


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
