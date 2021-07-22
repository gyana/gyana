import inspect

from apps.nodes.models import Node
from apps.nodes.nodes import NODE_FROM_CONFIG
from apps.tables.models import Table
from django.utils import timezone

from lib.clients import DATAFLOW_ID, bigquery_client


def get_all_parents(node: Node):
    # yield parents before child => topological order
    for parent in node.parents.all():
        yield from get_all_parents(parent)
    yield node


def validate_arity(func, len_args):

    node_arg, *params = inspect.signature(func).parameters.values()

    # testing for "*args" in signature
    if any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in params):
        assert len_args >= len(params) - 1
    else:
        assert len_args == len(params)


def get_query_from_node(node: Node):

    nodes = get_all_parents(node)
    # remove duplicates (python dicts are insertion ordered)
    nodes = list(dict.fromkeys(nodes))

    results = {}

    for node in nodes:
        func = NODE_FROM_CONFIG[node.kind]
        args = [results[parent] for parent in node.parents.all()]

        validate_arity(func, len(args))

        results[node] = func(node, *args)

    return results[node]


def create_or_replace_intermediate_table(table, node, query):
    """Creates a new intermediate table or replaces an existing one"""
    client = bigquery_client()
    if table:
        client.query(
            f"CREATE OR REPLACE TABLE {DATAFLOW_ID}.{table.bq_table} as ({query})"
        ).result()
        node.intermediate_table.data_updated = timezone.now()
        node.intermediate_table.save()
    else:
        table_id = f"table_pivot_{node.pk}"
        client.query(
            f"CREATE OR REPLACE TABLE {DATAFLOW_ID}.{table_id} as ({query})"
        ).result()

        table = Table(
            source=Table.Source.PIVOT_NODE,
            _bq_table=table_id,
            bq_dataset=DATAFLOW_ID,
            project=node.workflow.project,
            intermediate_node=node,
        )
        node.intermediate_table = table
        table.save()

    node.data_updated = timezone.now()
    node.save()

    return table


def get_parent_updated(node):
    """Walks through the node and its parents and returns the `data_updated` value."""
    yield node.data_updated

    # For an input node check whether the input_table has changed
    # e.g. whether a file has been synced again or a workflow ran
    if node.kind == "input":
        yield node.input_table.data_updated

    for parent in node.parents.all():
        yield from get_parent_updated(parent)
