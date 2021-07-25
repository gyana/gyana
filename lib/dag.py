import inspect
import logging

from apps.nodes.models import Node
from apps.nodes.nodes import NODE_FROM_CONFIG


def _get_all_parents(node: Node):
    # yield parents before child => topological order
    for parent in node.parents.all():
        yield from _get_all_parents(parent)
    yield node


def get_arity_from_node_func(func):

    node_arg, *params = inspect.signature(func).parameters.values()

    # testing for "*args" in signature
    variable_args = any(
        param.kind == inspect.Parameter.VAR_POSITIONAL for param in params
    )
    min_arity = len(params) - 1 if variable_args else len(params)

    return min_arity, variable_args


def _validate_arity(func, len_args):

    min_arity, variable_args = get_arity_from_node_func(func)
    assert len_args >= min_arity if variable_args else len_args == min_arity


def get_query_from_node(node: Node):

    nodes = _get_all_parents(node)
    # remove duplicates (python dicts are insertion ordered)
    nodes = list(dict.fromkeys(nodes))

    results = {}

    for node in nodes:
        func = NODE_FROM_CONFIG[node.kind]
        args = [results[parent] for parent in node.parents.all()]

        _validate_arity(func, len(args))

        try:
            results[node] = func(node, *args)
            if node.error:
                node.error = None
                node.save()
        except Exception as err:
            node.error = str(err)
            node.save()
            logging.error(err, exc_info=err)

        # input node zero state
        assert results[node] is not None

    return results[node]
