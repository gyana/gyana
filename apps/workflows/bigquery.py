import analytics
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.base import clients
from apps.base.analytics import WORFKLOW_RUN_EVENT
from apps.base.errors import error_name_to_snake
from apps.nodes.bigquery import NodeResultNone, get_query_from_node
from apps.nodes.models import Node
from apps.runs.models import JobRun
from apps.tables.models import Table


@shared_task(bind=True)
def run_workflow(self, run_id: int):
    run = JobRun.objects.get(pk=run_id)
    workflow = run.workflow
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

    if run.user:
        errors = {node.id: node.error for node in workflow.nodes.all() if node.error}
        analytics.track(
            run.user.id,
            WORFKLOW_RUN_EVENT,
            {
                "id": workflow.id,
                "success": not workflow.failed,
                **{
                    f"error_{idx}": errors[key] for idx, key in enumerate(errors.keys())
                },
            },
        )

    if workflow.failed:
        raise Exception
