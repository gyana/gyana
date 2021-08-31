from apps.dashboards.models import Dashboard
from apps.integrations.models import Integration
from apps.nodes.models import Node
from apps.projects.models import Project
from apps.templates.duplicate import get_instance_table_from_template_table
from apps.widgets.models import Widget
from apps.workflows.models import Workflow
from django import forms
from django.db import transaction

from .models import TemplateInstance, TemplateIntegration


class TemplateInstanceCreateForm(forms.ModelForm):
    class Meta:
        model = TemplateInstance
        fields = []

    def __init__(self, *args, **kwargs):
        self._team = kwargs.pop("team")
        self._template = kwargs.pop("template")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)

        project = Project(
            name=self._template.project.name,
            description=self._template.project.description,
            team=self._team,
        )

        instance.template = self._template
        instance.project = project

        # we only need templates for connectors, uploads and sheets are duplicated
        template_integrations = [
            TemplateIntegration(
                template_instance=instance, source_integration=integration
            )
            for integration in self._template.project.integration_set.filter(
                kind=Integration.Kind.CONNECTOR
            ).all()
        ]

        if commit:
            with transaction.atomic():
                project.save()
                instance.save()
                TemplateIntegration.objects.bulk_create(template_integrations)
                self.save_m2m()

        return instance


class TemplateInstanceUpdateForm(forms.ModelForm):
    class Meta:
        model = TemplateInstance
        fields = []

    def clean(self):
        if not self.instance.is_ready:
            raise forms.ValidationError("Not all data sources are ready yet.")

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:

            with transaction.atomic():

                # duplicate the project, new FKs where appropriate and delete
                cloned_project = instance.template.project.make_clone()

                workflows = list(cloned_project.workflow_set.all())
                for workflow in workflows:
                    workflow.project = instance.project

                dashboards = list(cloned_project.dashboard_set.all())
                for dashboard in dashboards:
                    dashboard.project = instance.project

                Dashboard.objects.bulk_update(dashboards, ["project"])
                Workflow.objects.bulk_update(workflows, ["project"])
                cloned_project.delete()

                # for each reference to an table, identify the new table
                input_nodes = Node.objects.filter(
                    workflow__project=instance.project,
                    input_table__integration__isnull=False,
                ).all()

                for input_node in input_nodes:
                    input_node.input_table = get_instance_table_from_template_table(
                        input_node.input_table, instance.project
                    )

                widgets = Widget.objects.filter(
                    dashboard__project=instance.project,
                    table__integration__isnull=False,
                ).all()

                for widget in widgets:
                    widget.table = get_instance_table_from_template_table(
                        widget.table, instance.project
                    )

                Node.objects.bulk_update(input_nodes, ["input_table"])
                Widget.objects.bulk_update(widgets, ["table"])

                # todo: run all the workflows

                # todo: directly duplicate Google Sheets and CSVs, for now

                instance.completed = True

                instance.save()
                self.save_m2m()

        return instance
