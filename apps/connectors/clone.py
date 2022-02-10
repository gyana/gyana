from django.db import transaction

from apps.base import clients


def update_schema(attrs, connector):
    """Adds new schema to `attrs` to avoid triggering the UniqueError on tables."""
    from apps.connectors.fivetran.client import create_schema

    attrs = attrs or {}
    team = connector.integration.project.team
    attrs["schema"] = create_schema(team.id, connector.service)
    return attrs


def create_fivetran(clone):
    client = clients.fivetran()
    transaction.on_commit(
        lambda: client.create(
            clone.service,
            clone.integration.project.team.id,
            clone.daily_sync_time,
            clone.schema,
        )
    )
