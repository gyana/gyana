def clone_connector(integration, integration_clone, using, cloned_references):
    """Explicitly adds connector and tables to clone"""

    # Cloning a o2o doesnt call the models `make_clone` so we call it explicitly here
    # https://github.com/tj-django/django-clone/issues/544
    if integration.kind == integration.Kind.CONNECTOR:
        integration.connector.make_clone(
            {"integration": integration_clone},
            using=using,
            cloned_references=cloned_references,
        )

    return integration_clone
