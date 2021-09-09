from apps.dashboards.models import Dashboard
from apps.integrations.models import Integration
from apps.projects.models import Project
from apps.tables.models import Table
from apps.templates.bigquery import copy_write_truncate_bq_table
from apps.templates.duplicate import get_target_table_from_source_table
from apps.widgets.models import Widget
from django import forms
from django.db import transaction

from .models import TemplateInstance, TemplateIntegration


class TemplateInstanceCreateNewForm(forms.ModelForm):
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
            ready=False,
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


class TemplateInstanceCreateExistingForm(forms.ModelForm):
    class Meta:
        model = TemplateInstance
        fields = ["project"]
        labels = {"project": "Choose a project"}

    def __init__(self, *args, **kwargs):
        self._team = kwargs.pop("team")
        self._template = kwargs.pop("template")
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = self._team.project_set.all()

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.template = self._template

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

                integrations = list(
                    cloned_project.integration_set.filter(
                        kind__in=[
                            Integration.Kind.SHEET,
                            Integration.Kind.UPLOAD,
                        ]
                    ).all()
                )
                for integration in integrations:
                    integration.project = instance.project

                # TODO: Templates with workflows in
                # workflows = list(cloned_project.workflow_set.all())
                # for workflow in workflows:
                #     workflow.project = instance.project

                dashboards = list(cloned_project.dashboard_set.all())
                for dashboard in dashboards:
                    dashboard.project = instance.project

                Integration.objects.bulk_update(integrations, ["project"])
                # Workflow.objects.bulk_update(workflows, ["project"])
                Dashboard.objects.bulk_update(dashboards, ["project"])

                # sheets + uploads tables

                # unfortunately, django-clone does not automatically update FK
                # references between duplicated entities. For example, the
                # duplication for a table and widget is:
                #   project -> integration_set -> table_set
                #   project -> dashboard_set -> widget_set
                # but the table_id in the widget does not point to the duplicated
                # table, but the original. We need to manually update these.
                # Plus we also need to point the connector tables to the new
                # connectors the user created as part of template creation.

                tables = Table.objects.filter(
                    integration__project=instance.project,
                    integration__kind__in=[
                        Integration.Kind.SHEET,
                        Integration.Kind.UPLOAD,
                    ],
                ).all()

                table_source_to_target = {}

                for table in tables:
                    # duplicated values have " copy X" appended to work with unique constraint
                    curr_table = Table.objects.filter(
                        bq_dataset=table.bq_dataset.split(" ")[0],
                        bq_table=table.bq_table.split(" ")[0],
                    ).first()
                    table.bq_dataset = instance.project.team.tables_dataset_id
                    table.bq_table = table.integration.source_obj.table_id
                    table.project = instance.project
                    table_source_to_target[curr_table] = table
                    copy_write_truncate_bq_table(curr_table.bq_id, table.bq_id)

                Table.objects.bulk_update(tables, ["bq_table", "bq_dataset", "project"])

                # connectors tables
                # for each reference to an table, identify the new table
                # input_nodes = Node.objects.filter(
                #     workflow__project=instance.project,
                #     input_table__integration__isnull=False,
                # ).all()

                # for input_node in input_nodes:
                #     input_node.input_table = (
                #         get_target_table_from_source_table(
                #             input_node.input_table, instance.project
                #         )
                #         if input_node.input_table.integration.kind
                #         == Integration.Kind.CONNECTOR
                #         else table_source_to_target[input_node.input_table]
                #     )

                widgets = Widget.objects.filter(
                    dashboard__project=instance.project,
                    table__integration__isnull=False,
                ).all()

                for widget in widgets:
                    widget.table = (
                        get_target_table_from_source_table(
                            widget.table, instance.project
                        )
                        if widget.table.integration.kind == Integration.Kind.CONNECTOR
                        else table_source_to_target[widget.table]
                    )

                # Node.objects.bulk_update(input_nodes, ["input_table"])
                Widget.objects.bulk_update(widgets, ["table"])

                # cascading delete for connectors
                cloned_project.delete()

                instance.completed = True

                instance.project.ready = True
                instance.project.save()
                instance.save()
                self.save_m2m()

            # for each workflow, we need to re-run the workflow and re-map
            # the output table for the downstream widgets and nodes to use
            # for workflow in workflows:
            #     run_workflow(workflow)

        return instance
