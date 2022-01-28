from django.utils import timezone


def clone_nodes(workflow, clone):
    node_map = {}

    nodes = workflow.nodes.all()
    # First create the mapping between original and cloned nodes
    for node in nodes:
        node_clone = node.make_clone({"workflow": clone})
        node_clone.data_updated = timezone.now()
        # TODO: replace with bulkupdate
        node_clone.save()
        node_map[node] = node_clone

    # Then copy the relationships
    for node in nodes:
        node_clone = node_map[node]
        for parent in node.parent_edges.iterator():
            node_clone.parent_edges.create(
                parent_id=node_map[parent.parent].id, position=parent.position
            )
