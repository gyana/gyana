from django.db import transaction
from django.utils import timezone

from apps.base.clients import get_engine
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
    with transaction.atomic():
        table, _ = Table.objects.get_or_create(
            source=Table.Source.INTERMEDIATE_NODE,
            name=node.bq_intermediate_table_id,
            namespace=node.workflow.project.team.tables_dataset_id,
            project=node.workflow.project,
            intermediate_node=node,
        )

        get_engine().create_or_replace_table(table.fqn, query.compile())

        table.data_updated = timezone.now()
        table.save()
    return table
