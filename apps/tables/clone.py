from django.db import transaction

from apps.base import clients
from apps.base.bigquery import copy_table


def create_attrs(attrs, original):
    """Depending on a table's source the bq_table and bq_dataset need to be updated.
    By default django-clone adds `copy {number}` to these because of the unique constraint.
    We also manually set the deoendency to a potentially new project
    """
    from apps.integrations.models import Integration

    attrs = attrs or {}
    attrs["copied_from"] = original.id
    if original.source == original.Source.INTEGRATION and (
        integration_clone := attrs.get("integration")
    ):
        attrs["project"] = integration_clone.project
        if integration_clone.kind in [
            Integration.Kind.UPLOAD,
            Integration.Kind.SHEET,
            Integration.Kind.CUSTOMAPI,
        ]:
            # For these simply use the new source table_id and the original team_dataset
            attrs["bq_table"] = integration_clone.source_obj.table_id
            attrs["bq_dataset"] = original.bq_dataset
        elif integration_clone.kind == Integration.Kind.CONNECTOR:
            # Connectors should have a new dataset created but the table name stays the same
            attrs["bq_table"] = original.bq_table
            # We are replacing the connector schema from the bq_dataset to
            # To maintain schema names for e.g. database connectors.
            attrs["bq_dataset"] = original.bq_dataset.replace(
                original.integration.connector.bq_dataset_prefix,
                integration_clone.connector.bq_dataset_prefix,
            )

    # Dependies to nodes simply stay in the same dataset but change the table name
    elif original.source == original.Source.WORKFLOW_NODE:
        clone_node = attrs["workflow_node"]
        attrs["project"] = clone_node.workflow.project
        attrs["bq_table"] = clone_node.bq_output_table_id
        attrs["bq_dataset"] = original.bq_dataset
    elif original.source == original.Source.INTERMEDIATE_NODE:
        clone_node = attrs["intermediate_node"]
        attrs["project"] = clone_node.workflow.project
        attrs["bq_table"] = clone_node.bq_intermediate_table_id
        attrs["bq_dataset"] = original.bq_dataset
    elif original.source == original.Source.CACHE_NODE:
        clone_node = attrs["cache_node"]
        attrs["project"] = clone_node.workflow.project
        attrs["bq_table"] = clone_node.bq_cache_table_id
        attrs["bq_dataset"] = original.bq_dataset

    return attrs


# Make sure this is called inside a celery task, it could take a while
def duplicate_table(original, clone):
    if (
        clone.source == clone.Source.INTEGRATION
        and clone.integration.kind == clone.integration.Kind.CONNECTOR
    ):
        client = clients.bigquery()
        transaction.on_commit(
            lambda: client.create_dataset(  # Create dataset if it doesn't exist yet
                clone.bq_dataset, exists_ok=True
            )
        )
    transaction.on_commit(lambda: copy_table(original.bq_id, clone.bq_id).result())
