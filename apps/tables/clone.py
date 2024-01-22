from django.db import transaction

from apps.base.clients import get_engine


def create_attrs(attrs, original):
    """Depending on a table's source the `name` and namespace need to be updated.
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
            attrs["name"] = integration_clone.source_obj.table_id
            attrs["namespace"] = original.namespace

    # Dependies to nodes simply stay in the same dataset but change the table name
    elif original.source == original.Source.WORKFLOW_NODE:
        clone_node = attrs["workflow_node"]
        attrs["project"] = clone_node.workflow.project
        attrs["name"] = clone_node.bq_output_table_id
        attrs["namespace"] = original.namespace
    elif original.source == original.Source.INTERMEDIATE_NODE:
        clone_node = attrs["intermediate_node"]
        attrs["project"] = clone_node.workflow.project
        attrs["name"] = clone_node.bq_intermediate_table_id
        attrs["namespace"] = original.namespace
    elif original.source == original.Source.CACHE_NODE:
        clone_node = attrs["cache_node"]
        attrs["project"] = clone_node.workflow.project
        attrs["name"] = clone_node.bq_cache_table_id
        attrs["namespace"] = original.namespace

    return attrs


# Make sure this is called inside a celery task, it could take a while
def duplicate_table(original, clone):
    transaction.on_commit(lambda: get_engine().copy_table(original.fqn, clone.fqn))
