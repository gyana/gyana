def update_schema(attrs, connector):
    from apps.connectors.fivetran.client import create_schema

    attrs = attrs or {}
    team = connector.integration.project.team
    attrs["schema"] = create_schema(team.id, connector.service)
    return attrs
