from django.db import transaction

from apps.base import clients


def update_schema(attrs, connector):
    """Adds new schema to `attrs` to avoid triggering the UniqueError on tables."""
    from apps.connectors.fivetran.client import create_schema

    attrs = attrs or {}
    team = connector.integration.project.team
    attrs["schema"] = create_schema(team.id, connector.service)
    return attrs


def clone_fivetran_instance(original, clone):
    from apps.connectors.fivetran.client import SYNC_FREQUENCY

    client = clients.fivetran()
    original_config = client.get(original)
    clone_config = {
        "group_id": original_config["group_id"],
        "schema": clone.schema,
        "trust_certificates": True,
        "run_setup_tests": False,
        "sync_frequency": SYNC_FREQUENCY,
        "service": original_config["service"],
        "daily_sync_time": original_config.get(
            "daily_sync_time", original.daily_sync_time
        ),
        "config": {"schema": clone.schema, **original_config["config"]},
    }
    res = client.new(clone_config)
    clone.update_kwargs_from_fivetran(res["data"])
    clone.save()


def create_fivetran(original, clone):
    transaction.on_commit(lambda: clone_fivetran_instance(original, clone))
