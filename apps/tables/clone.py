def create_attrs(attrs, original):
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

            attrs["bq_table"] = integration_clone.source_obj.table_id
            attrs["bq_dataset"] = original.bq_dataset
        elif integration_clone.kind == Integration.Kind.CONNECTOR:
            attrs["bq_table"] = original.bq_table
            attrs["bq_dataset"] = original.bq_dataset.replace(
                original.integration.connector.schema,
                integration_clone.connector.schema,
            )

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
