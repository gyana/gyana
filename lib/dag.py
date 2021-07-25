import inspect
import logging

from apps.nodes.models import Node
from apps.tables.models import Table
from django.utils import timezone

from lib.clients import DATAFLOW_ID, bigquery_client, ibis_client


def _get_all_parents(node: Node):
    # yield parents before child => topological order
    for parent in node.parents.all():
        yield from _get_all_parents(parent)
    yield node


def _validate_arity(func, len_args):

    node_arg, *params = inspect.signature(func).parameters.values()

    # testing for "*args" in signature
    if any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in params):
        assert len_args >= len(params) - 1
    else:
        assert len_args == len(params)


def get_query_from_node(node: Node):

    from apps.nodes.nodes import NODE_FROM_CONFIG

    nodes = _get_all_parents(node)
    # remove duplicates (python dicts are insertion ordered)
    nodes = list(dict.fromkeys(nodes))

    results = {}

    for node in nodes:
        func = NODE_FROM_CONFIG[node.kind]
        args = [results[parent] for parent in node.parents.all()]

        _validate_arity(func, len(args))

        results[node] = func(node, *args)

        try:
            query = get_query_from_node(node)
            if node.error:
                node.error = None
                node.save()
            return query
        except Exception as err:
            node.error = str(err)
            node.save()
            logging.error(err, exc_info=err)

        # input node zero state
        assert results[node] is not None

    return results[node]


def _create_or_replace_intermediate_table(table, node, query):
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


def _get_parent_updated(node):
    """Walks through the node and its parents and returns the `data_updated` value."""
    yield node.data_updated

    # For an input node check whether the input_table has changed
    # e.g. whether a file has been synced again or a workflow ran
    if node.kind == "input":
        yield node.input_table.data_updated

    for parent in node.parents.all():
        yield from _get_parent_updated(parent)


def use_intermediate_table(func):
    def wrapper(node, parent):

        table = node.intermediate_table
        conn = ibis_client()

        # if the table doesn't need updating we can simply return the previous computed pivot table
        if table and table.data_updated > max(tuple(_get_parent_updated(node))):
            return conn.table(table.bq_table, database=table.bq_dataset)

        query = func(node, parent)
        table = _create_or_replace_intermediate_table(table, node, query)

        return conn.table(table.bq_table, database=table.bq_dataset)

    return wrapper
