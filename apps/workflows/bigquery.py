from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.base import clients
from apps.base.errors import error_name_to_snake
from apps.nodes.bigquery import NodeResultNone, get_query_from_node
from apps.nodes.models import Node
from apps.tables.models import Table
from apps.workflows.models import Workflow


@shared_task(bind=True)
def run_workflow(self, workflow_id: int):
    workflow = Workflow.objects.get(pk=workflow_id)
    output_nodes = workflow.nodes.filter(kind=Node.Kind.OUTPUT).all()
    client = clients.bigquery()

    for node in output_nodes:
        try:
            query = get_query_from_node(node)
        except NodeResultNone as err:
            node.error = error_name_to_snake(err)
            node.save()
            query = None
        if query is not None:

            with transaction.atomic():

                table, _ = Table.objects.get_or_create(
                    source=Table.Source.WORKFLOW_NODE,
                    bq_table=node.bq_output_table_id,
                    bq_dataset=workflow.project.team.tables_dataset_id,
                    project=workflow.project,
                    workflow_node=node,
                )

                client.query(
                    f"CREATE OR REPLACE TABLE {table.bq_id} as ({query.compile()})"
                ).result()

                table.data_updated = timezone.now()
                table.save()

    if workflow.failed:
        raise Exception
