import inspect

from apps.nodes.models import Node
from apps.nodes.nodes import NODE_FROM_CONFIG
from ibis.expr.types import param


def get_all_parents(node: Node):
    # yield parents before child => topological order
    for parent in node.parents.all():
        yield from get_all_parents(parent)
    yield node


def validate_arity(func, len_args):

    _, *params = inspect.signature(func).parameters.values()

    if len(params) == 0:
        assert len_args == 0
    # testing for "*args" in signature
    elif any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in params):
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
