from apps.integrations.models import Integration
from django.urls.base import reverse


def _get_template_integration_in_project(template_integration, project):
    qs = project.integration_set.filter(kind=template_integration.kind)
    if template_integration.kind == Integration.Kind.CONNECTOR:
        qs = qs.filter(connector__service=template_integration.connector.service)
    return qs


def template_integration_exists_in_project(template_integration, project):
    return _get_template_integration_in_project(template_integration, project).exists()


def template_integration_is_ready_in_project(template_integration, project):
    return (
        _get_template_integration_in_project(template_integration, project)
        .filter(ready=True)
        .exists()
    )


def get_instance_table_from_template_table(template_table, project):
    template_integration = template_table.integration
    # for now, we just choose the first matching integration
    # in future, possibly let user decide the mapping
    project_integration = _get_template_integration_in_project(
        template_integration
    ).first()

    # this would fail if the user decided not to sync certain tables from the schema across
    return project_integration.table_set.filter(
        bq_table=template_table.bq_table
    ).first()


def get_create_url_in_project(template_integration, project):
    if template_integration.kind == Integration.Kind.CONNECTOR:
        return f'{reverse("project_integrations_connectors:create", args=(project.id,))}?service={template_integration.connector.service}'
    if template_integration.kind == Integration.Kind.SHEET:
        return reverse("project_integrations_sheets:create", args=(project.id,))
    if template_integration.kind == Integration.Kind.UPLOAD:
        return reverse("project_integrations_uploads:create", args=(project.id,))
