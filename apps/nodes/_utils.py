from django.db import transaction
from django.utils import timezone

from apps.base import clients
from apps.tables.models import Table


def get_parent_updated(node):
    """Walks through the node and its parents and returns the `data_updated` value."""
    yield node.data_updated

    # For an input node check whether the input_table has changed
    # e.g. whether a file has been synced again or a workflow ran
    if node.kind == "input":
        yield node.input_table.data_updated

    for parent in node.parents.all():
        yield from get_parent_updated(parent)


def create_or_replace_intermediate_table(node, query):
    """Creates a new intermediate table or replaces an existing one"""
    client = clients.bigquery()

    with transaction.atomic():
        table, _ = Table.objects.get_or_create(
            source=Table.Source.INTERMEDIATE_NODE,
            bq_table=node.bq_intermediate_table_id,
            bq_dataset=node.workflow.project.team.tables_dataset_id,
            project=node.workflow.project,
            intermediate_node=node,
        )

        client.query(f"CREATE OR REPLACE TABLE {table.bq_id} as ({query})").result()

        node.intermediate_table = table
        node.save()

        table.data_updated = timezone.now()
        table.save()
    return table
