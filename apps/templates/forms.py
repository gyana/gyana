from apps.dashboards.models import Dashboard
from apps.projects.models import Project
from apps.workflows.models import Workflow
from django import forms
from django.db import transaction

from .models import TemplateInstance


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

        if commit:
            with transaction.atomic():
                project.save()
                instance.save()
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

        # duplicate the project, assign workflows and to new project and throwaway
        cloned_project = instance.template.project.make_clone()

        workflows = list(cloned_project.workflow_set.all())
        for workflow in workflows:
            workflow.project = instance.project

        dashboards = list(cloned_project.dashboard_set.all())
        for dashboard in dashboards:
            dashboard.project = instance.project

        instance.completed = True

        if commit:
            with transaction.atomic():
                instance.save()
                Dashboard.objects.bulk_update(dashboards, ["project"])
                Workflow.objects.bulk_update(workflows, ["project"])
                cloned_project.delete()
                self.save_m2m()

        return instance
