from apps.projects.models import Project
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

        # duplicate the project

        instance.completed = True

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()

        return instance
