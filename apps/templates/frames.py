from apps.base.frames import TurboFrameUpdateView
from apps.templates.duplicate import (
    get_create_url_in_project,
    template_integration_exists_in_project,
)
from apps.templates.forms import TemplateInstanceUpdateForm
from django_tables2.views import MultiTableMixin

from .models import TemplateInstance
from .tables import TemplateInstanceIntegrationTable, TemplateInstanceSetupTable


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
                "setup": get_create_url_in_project(t, self.object.project),
            }
            for t in self.object.template.project.integration_set.all()
            if not template_integration_exists_in_project(t, self.object.project)
        ]

        project_integrations = self.object.project.integration_set.all()

        return [template_integrations, project_integrations]
