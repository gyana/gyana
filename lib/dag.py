from apps.nodes.models import Node
from apps.nodes.nodes import NODE_FROM_CONFIG


def get_all_parents(node: Node):
    for parent in node.parents.all():
        yield from get_all_parents(parent)
    yield node


def get_query_from_node(node: Node):

    nodes = get_all_parents(node)
    # python dicts are insertion ordered and unique
    nodes = list(dict.fromkeys(nodes))

    results = {}

    for node in nodes:
        func = NODE_FROM_CONFIG[node.kind]
        args = [results[parent] for parent in node.parents.all()]
        results[node] = func(*args)

    return results[node]
