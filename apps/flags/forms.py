from django import forms
from django.forms.models import ModelMultipleChoiceField

from apps.teams.models import Team

from .models import Flag


class TeamFlagForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["flags"]

    flags = ModelMultipleChoiceField(
        queryset=Flag.objects.all(), widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["flags"].initial = self.instance.flags.all().values_list(
            "id", flat=True
        )

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)

        instance.flags.set(self.cleaned_data["flags"])

        return instance
