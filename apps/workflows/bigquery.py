from apps.nodes.models import Node
from apps.tables.models import Table
from apps.workflows.models import Workflow
from django.utils import timezone
from apps.base.clients import DATAFLOW_ID, bigquery_client
from apps.nodes.bigquery import get_query_from_node


def run_workflow(workflow: Workflow):
    output_nodes = workflow.nodes.filter(kind=Node.Kind.OUTPUT).all()

    for node in output_nodes:
        client = bigquery_client()
        query = get_query_from_node(node)
        if query is not None:
            query = query.compile()

            try:
                client.query(
                    f"CREATE OR REPLACE TABLE {DATAFLOW_ID}.{node.table.bq_table} as ({query})"
                ).result()
                node.table.data_updated = timezone.now()
                node.table.save()

            except Table.DoesNotExist:
                table_id = f"table_{node.pk}"
                client.query(
                    f"CREATE OR REPLACE TABLE {DATAFLOW_ID}.{table_id} as ({query})"
                ).result()

                table = Table(
                    source=Table.Source.WORKFLOW_NODE,
                    _bq_table=table_id,
                    bq_dataset=DATAFLOW_ID,
                    project=workflow.project,
                    workflow_node=node,
                )
                table.save()

    if workflow.failed:
        return {node.id: node.error for node in workflow.nodes.all() if node.error}

    workflow.last_run = timezone.now()
    # Use fields to not trigger auto_now on the updated field
    workflow.save(update_fields=["last_run"])
