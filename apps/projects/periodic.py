from graphlib import CycleError, TopologicalSorter

from celery import shared_task

from apps.base.tasks import honeybadger_check_in
from apps.connectors.models import Connector
from apps.nodes.models import Node
from apps.projects.models import Project
from apps.sheets.models import Sheet
from apps.tables.models import Table
from apps.workflows.models import Workflow

from .models import Project

# Retry every 10 minutes for next 6 hours, this will continue to try until
# the incremental connector resyncs are completed.
RETRY_COUNTDOWN = 60 * 10
MAX_RETRIES = 3600 / RETRY_COUNTDOWN * 24


def _get_entity_from_input_table(table: Table):
    if table.source == Table.Source.WORKFLOW_NODE:
        return table.workflow_node.workflow
    else:
        return table.integration.source_obj


@shared_task(bind=True)
def run_schedule_for_project(self, project_id: int):

    project = Project.objects.get(pk=project_id)

    project.update_schedule()

    # skip workflow if nothing to run
    if project.periodic_task is None:
        return

    # Run all the workflows in a project. The python graphlib library will build
    # a topological sort for any graph of hashables and raises a cycle error if
    # there is a circularity.

    workflows = Workflow.objects.is_scheduled_in_project(project).all()

    # one query per workflow, in future we would optimize into a single query
    graph = {
        workflow: [
            _get_entity_from_input_table(node.input_table)
            for node in workflow.nodes.filter(kind=Node.Kind.INPUT)
            .select_related("input_table__workflow_node__workflow")
            .select_related("input_table__integration__sheet")
            .select_related("input_table__integration__connector")
            .all()
        ]
        for workflow in workflows
    }

    graph.update(
        {sheet: [] for sheet in Sheet.objects.is_scheduled_in_project(project).all()}
    )

    ts = TopologicalSorter(graph)

    retry = False

    try:
        for entity in ts.static_order():

            # Run a step when all the previous steps have run (even if they failed,
            # to keep it simple we don't propagate "blocked" information). This
            # is designed to be idempotent, we can keep running this task until
            # everything has completed successfully.

            for e in graph[entity]:
                e.refresh_from_db()

            scheduled_parents = [
                e
                for e in graph[entity]
                if (hasattr(e, "is_scheduled") and e.is_scheduled)
                # connectors are always scheduled
                or isinstance(e, Connector)
            ]

            if any(not e.up_to_date for e in scheduled_parents):
                retry = True

            if (
                hasattr(entity, "is_scheduled")
                and entity.is_scheduled
                and not entity.up_to_date
                and all(e.up_to_date for e in scheduled_parents)
            ):
                entity.run_for_schedule()

    except CycleError:
        # todo: add an error to the schedule to track "is_circular"
        pass

    # We need to keep retrying until the connectors either fail or succeeded
    if retry:
        self.retry(countdown=RETRY_COUNTDOWN, max_retries=MAX_RETRIES)

    honeybadger_check_in("j6IrRd")
