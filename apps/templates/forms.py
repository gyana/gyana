from apps.base.clients import bigquery_client
from apps.dashboards.models import Dashboard
from apps.integrations.models import Integration
from apps.nodes.models import Node
from apps.projects.models import Project
from apps.tables.models import Table
from apps.templates.duplicate import get_target_table_from_source_table
from apps.widgets.models import Widget
from apps.workflows.bigquery import run_workflow
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

                # sheets + uploads tables

                tables = cloned_project.table_set.filter(
                    integration__kind__in=[
                        Integration.Kind.SHEET,
                        Integration.Kind.UPLOAD,
                    ],
                ).all()

                for table in tables:
                    # duplicated values have " copy X" appended to work with unique constraint
                    curr_bq_id = f"{table.bq_dataset.split(' ')[0]}.{table.bq_table.split(' ')[0]}"
                    table.bq_dataset = instance.project.team.tables_dataset_id
                    table.bq_table = table.integration.source_obj.table_id
                    table.project = instance.project
                    bigquery_client().copy_table(curr_bq_id, table.bq_id)

                Table.objects.bulk_update(tables, ["bq_table", "bq_dataset", "project"])

                # connectors tables
                # for each reference to an table, identify the new table
                input_nodes = Node.objects.filter(
                    workflow__project=instance.project,
                    input_table__integration__isnull=False,
                    table__integration__kind=Integration.Kind.CONNECTOR,
                ).all()

                for input_node in input_nodes:
                    input_node.input_table = get_target_table_from_source_table(
                        input_node.input_table, instance.project
                    )

                widgets = Widget.objects.filter(
                    dashboard__project=instance.project,
                    table__integration__isnull=False,
                    table__integration__kind=Integration.Kind.CONNECTOR,
                ).all()

                for widget in widgets:
                    widget.table = get_target_table_from_source_table(
                        widget.table, instance.project
                    )

                Node.objects.bulk_update(input_nodes, ["input_table"])
                Widget.objects.bulk_update(widgets, ["table"])

                # cascading delete for connectors
                cloned_project.delete()

                instance.completed = True

                instance.save()
                self.save_m2m()

            # TODO: run within celery progress with streaming update
            for workflow in workflows:
                run_workflow(workflow)

        return instance
