from uuid import uuid4

import analytics
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.base.analytics import WORFKLOW_RUN_EVENT
from apps.base.clients import get_engine
from apps.base.core.utils import error_name_to_snake
from apps.nodes.bigquery import NodeResultNone, get_query_from_node
from apps.nodes.models import Node
from apps.runs.models import JobRun
from apps.tables.models import Table
from apps.users.models import CustomUser

from .models import Workflow


@shared_task(bind=True)
def run_workflow_task(self, run_id: int):
    run = JobRun.objects.get(pk=run_id)
    workflow = run.workflow
    output_nodes = workflow.nodes.filter(kind=Node.Kind.OUTPUT).all()

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
                get_engine().create_or_replace_table(table.bq_id, query.compile())

                table.data_updated = timezone.now()
                table.save()

    if run.user:
        analytics.track(
            run.user.id,
            WORFKLOW_RUN_EVENT,
            {"id": workflow.id, "success": not workflow.failed},
        )

    if workflow.failed:
        raise Exception


def run_workflow(workflow: Workflow, user: CustomUser):
    run = JobRun.objects.create(
        source=JobRun.Source.WORKFLOW,
        workflow=workflow,
        task_id=uuid4(),
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
        user=user,
    )
    run_workflow_task.apply_async((run.id,), task_id=str(run.task_id))
    return run
