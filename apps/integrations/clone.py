def clone_connector_and_tables(integration, integration_clone, using):
    """Explicitly adds connector and tables to clone"""

    # Cloning a o2o doesnt call the models `make_clone` so we call it explicitly here
    # https://github.com/tj-django/django-clone/issues/544
    if integration.kind == integration.Kind.CONNECTOR:
        integration.connector.make_clone(
            {"integration": integration_clone}, using=using
        )
    # We need to do this after the connector has been created
    for table in integration.table_set.all():
        table.make_clone({"integration": integration_clone}, using=using)
    return integration_clone
