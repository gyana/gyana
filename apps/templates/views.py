from functools import cached_property

from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.projects.mixins import ProjectMixin
from apps.teams.mixins import TeamMixin
from apps.templates.duplicate import (
    get_create_url_in_project,
    template_integration_exists_in_project,
)
from apps.templates.forms import TemplateInstanceUpdateForm
from django.shortcuts import redirect
from django.urls.base import reverse
from django_tables2 import SingleTableView
from django_tables2.views import MultiTableMixin

from .forms import TemplateInstanceCreateForm
from .models import Template, TemplateInstance
from .tables import (
    TemplateInstanceIntegrationTable,
    TemplateInstanceSetupTable,
    TemplateInstanceTable,
    TemplateTable,
)


class TemplateList(TeamMixin, SingleTableView):
    template_name = "templates/list.html"
    model = Template
    table_class = TemplateTable
    paginate_by = 20


class TemplateInstanceCreate(TeamMixin, TurboCreateView):
    template_name = "templateinstances/create.html"
    model = TemplateInstance
    form_class = TemplateInstanceCreateForm

    @cached_property
    def template(self):
        return Template.objects.get(pk=self.kwargs["template_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template"] = self.template
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.team
        kwargs["template"] = self.template
        return kwargs

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.project.id,))


class TemplateInstanceList(ProjectMixin, SingleTableView):
    template_name = "templateinstances/list.html"
    model = TemplateInstance
    table_class = TemplateInstanceTable
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        if self.project.templateinstance_set.count() <= 1:
            return redirect(
                "project_templateinstances:detail",
                self.project.id,
                self.project.templateinstance_set.first().id,
            )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.project.templateinstance_set.all()


class TemplateInstanceUpdate(ProjectMixin, MultiTableMixin, TurboUpdateView):
    template_name = "templateinstances/update.html"
    model = TemplateInstance
    form_class = TemplateInstanceUpdateForm
    tables = [TemplateInstanceSetupTable, TemplateInstanceIntegrationTable]
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

    def get_success_url(self):
        return reverse("projects:detail", args=(self.project.id,))
