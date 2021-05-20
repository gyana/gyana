from datetime import datetime

from apps.tables.models import Table
from apps.workflows.models import Node, Workflow
from lib.clients import DATAFLOW_ID, bigquery_client


def run_workflow(workflow: Workflow):
    output_nodes = workflow.nodes.filter(kind=Node.Kind.OUTPUT).all()

    for node in output_nodes:
        client = bigquery_client()
        query = node.get_query()
        if query is not None:
            query = query.compile()

            try:
                client.query(
                    f"CREATE OR REPLACE TABLE {DATAFLOW_ID}.{node.table.bq_table} as ({query})"
                ).result()
                node.table.data_updated = datetime.now()
                node.table.save()

            except Table.DoesNotExist:
                table_id = f"table_{node.pk}"
                client.query(
                    f"CREATE OR REPLACE TABLE {DATAFLOW_ID}.{table_id} as ({query})"
                ).result()

                table = Table(
                    source=Table.Source.WORKFLOW_NODE,
                    bq_table=table_id,
                    bq_dataset=DATAFLOW_ID,
                    project=workflow.project,
                    workflow_node=node,
                )
                table.save()

    workflow.last_run = datetime.now()
