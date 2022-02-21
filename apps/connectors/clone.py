from django.db import transaction

from apps.base import clients


def update_schema(attrs, connector):
    """Adds new schema to `attrs` to avoid triggering the UniqueError on tables."""
    from apps.connectors.fivetran.client import create_schema

    attrs = attrs or {}
    team = connector.integration.project.team
    attrs["schema"] = create_schema(team.id, connector.service)
    return attrs


def clone_fivetran_instance(clone):
    client = clients.fivetran()
    data = client.create(
        clone.service,
        clone.integration.project.team.id,
        clone.daily_sync_time,
        clone.schema,
    )
    clone.update_kwargs_from_fivetran(data)
    clone.save()


def create_fivetran(clone):
    transaction.on_commit(lambda: clone_fivetran_instance(clone))
