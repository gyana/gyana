def clone_tables(node, clone):
    if node.kind == node.Kind.OUTPUT and hasattr(node, "table"):
        node.table.make_clone({"workflow_node": clone}, sub_clone=True, using=clone)
    elif node.intermediate_table:
        node.intermediate_table.make_clone(
            {"intermediate_node": clone}, sub_clone=True, using=clone
        )
    elif node.cache_table:
        node.cache_table.make_clone({"cache_node": clone}, sub_clone=True, using=clone)
