from apps.base.frames import TurboFrameUpdateView
from apps.integrations.models import Integration
from apps.templates.forms import TemplateInstanceUpdateForm
from django.urls.base import reverse
from django_tables2.views import MultiTableMixin

from .models import TemplateInstance
from .tables import TemplateInstanceIntegrationTable, TemplateInstanceSetupTable


def _template_integration_exists_in_project(template_integration, project):
    qs = project.integration_set.filter(kind=template_integration.kind)
    if template_integration.kind == Integration.Kind.CONNECTOR:
        qs = qs.filter(connector__service=template_integration.connector.service)
    return qs.exists()


def _get_create_url_in_project(template_integration, project):
    if template_integration.kind == Integration.Kind.CONNECTOR:
        return f'{reverse("project_integrations_connectors:create", args=(project.id,))}?service={template_integration.connector.service}'
    if template_integration.kind == Integration.Kind.SHEET:
        return reverse("project_integrations_sheets:create", args=(project.id,))
    if template_integration.kind == Integration.Kind.UPLOAD:
        return reverse("project_integrations_uploads:create", args=(project.id,))


class TemplateInstanceSetup(MultiTableMixin, TurboFrameUpdateView):
    template_name = "templates/setup.html"
    model = TemplateInstance
    form_class = TemplateInstanceUpdateForm
    tables = [TemplateInstanceSetupTable, TemplateInstanceIntegrationTable]
    turbo_frame_dom_id = "template:setup"
    table_pagination = False

    def get_tables(self):
        return [
            table(data, show_header=False)
            for table, data in zip(self.tables, self.get_table_data())
        ]

    def get_table_data(self):

        template_integrations = [
            {
                "icon": t.icon,
                "name": t.name,
                "setup": _get_create_url_in_project(t, self.object.project),
            }
            for t in self.object.template.project.integration_set.all()
            if not _template_integration_exists_in_project(t, self.object.project)
        ]

        project_integrations = self.object.project.integration_set.all()

        return [template_integrations, project_integrations]
