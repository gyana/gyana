from apps.projects.models import Project
from apps.tables.models import Table


def get_target_table_from_source_table(source_table: Table, project: Project):

    # find the corresponding integration in the new project
    template_integration = (
        source_table.integration.template_integration_source_set.filter(
            template_instance__project=project
        ).first()
    )

    if template_integration is None:
        return None

    # the assumption is to map the table names between integrations
    return template_integration.target_integration.table_set.filter(
        bq_table=source_table.bq_table
    ).first()
