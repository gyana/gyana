def clone_tables(node, clone, using):
    # Cloning a o2o doesnt call the models `make_clone` so we call it explicitly here
    # https://github.com/tj-django/django-clone/issues/544
    if node.kind == node.Kind.OUTPUT and hasattr(node, "table"):
        node.table.make_clone({"workflow_node": clone}, using=using)
    elif node.intermediate_table:
        node.intermediate_table.make_clone({"intermediate_node": clone}, using=using)
    elif node.cache_table:
        node.cache_table.make_clone({"cache_node": clone}, using=using)
