from typing import Final

import analytics

from apps.nodes.models import Edge, Node
from apps.users.models import CustomUser

# users
SIGNED_UP_EVENT: Final = "Signed up"
ONBOARDING_COMPLETED_EVENT: Final = "Onboarding completed"

# teams
TEAM_CREATED_EVENT: Final = "Team created"
INVITE_SENT_EVENT: Final = "Invite sent"
INVITE_ACCEPTED_EVENT: Final = "Invite accepted"

# projects
PROJECT_CREATED_EVENT: Final = "Project created"
PROJECT_RUN_EVENT: Final = "Project run"

# templates
TEMPLATE_VIEWED_EVENT: Final = "Template viewed"
TEMPLATE_CREATED_EVENT: Final = "Template created"
TEMPLATE_COMPLETED_EVENT: Final = "Template completed"

# integrations
NEW_INTEGRATION_START_EVENT: Final = "New integration started"
INTEGRATION_CREATED_EVENT: Final = "Integration created"
INTEGRATION_AUTHORIZED_EVENT: Final = "Integration authorized"
INTEGRATION_SYNC_STARTED_EVENT: Final = "Integration sync started"
INTEGRATION_SYNC_SUCCESS_EVENT: Final = "Integration sync succeeded"

# workflows
WORKFLOW_CREATED_EVENT: Final = "Workflow created"
WORKFLOW_CREATED_EVENT_FROM_INTEGRATION: Final = "Workflow created from integration"
WORKFLOW_DUPLICATED_EVENT: Final = "Workflow duplicated"
NODE_CREATED_EVENT: Final = "Node created"
NODE_UPDATED_EVENT: Final = "Node updated"
NODE_CONNECTED_EVENT: Final = "Node connected"
NODE_PREVIEWED_EVENT: Final = "Node previewed"
NODE_COMPLETED_EVENT: Final = "Node completed"
WORFKLOW_RUN_EVENT: Final = "Workflow run"

# dashboards
DASHBOARD_CREATED_EVENT: Final = "Dashboard created"
DASHBOARD_CREATED_EVENT_FROM_INTEGRATION: Final = "Dashboard created from integration"
DASHBOARD_DUPLICATED_EVENT: Final = "Dashboard duplicated"
WIDGET_CREATED_EVENT: Final = "Widget created"
WIDGET_DUPLICATED_EVENT: Final = "Widget duplicated"
WIDGET_CONFIGURED_EVENT: Final = "Widget configured"
WIDGET_PREVIEWED_EVENT: Final = "Widget previewed"
WIDGET_COMPLETED_EVENT: Final = "Widget completed"
DASHBOARD_SHARED_PUBLIC_EVENT: Final = "Dashboard shared public"

# subscriptions
CHECKOUT_OPENED_EVENT: Final = "Checkout opened"
CHECKOUT_COMPLETED_EVENT: Final = "Checkout completed"
SUBSCRIPTION_CREATED_EVENT: Final = "Subscription created"
SUBSCRIPTION_UPDATED_EVENT: Final = "Subscription updated"
SUBSCRIPTION_CANCELLED_EVENT: Final = "Subscription cancelled"

# exports
EXPORT_CREATED: Final = "Export created"


def identify_user(user: CustomUser, signup_source=None):

    traits = {
        "username": user.username,
        "name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        # TODO: add plan information here
    }

    if signup_source is not None:
        # waitlist OR invite OR website
        traits["signup_source"] = signup_source

    analytics.identify(user.id, traits)


def identify_user_group(user: CustomUser, team):
    analytics.group(
        user.id,
        team.id,
        {"name": team.name},
    )


def track_node(user: CustomUser, node: Node, track_id: str, **kwargs):
    """Sends tracking event with default fields. Allows for kwargs to be added as additional properties"""
    analytics.track(
        user.id,
        track_id,
        {"id": node.id, "type": node.kind, "workflow_id": node.workflow.id, **kwargs},
    )


def track_edge(user: CustomUser, edge: Edge, track_id: str, **kwargs):
    """Sends tracking event with default fields. Allows for kwargs to be added as additional properties"""
    analytics.track(
        user.id,
        track_id,
        {
            # legacy
            "id": edge.child.id,
            "type": edge.child.kind,
            "workflow_id": edge.child.workflow_id,
            # new from 29/11/2021
            "edge_id": edge.id,
            "parent": edge.parent.id,
            "child": edge.child.id,
            "parent_kind": edge.parent.kind,
            "child_kind": edge.child.kind,
        },
        **kwargs,
    )
