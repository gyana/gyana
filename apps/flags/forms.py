from django import forms
from django.forms.models import ModelMultipleChoiceField

from apps.teams.models import Team

from .models import Flag
from .widgets import FlagCheckboxSelectMultiple


class TeamFlagForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["flags"]

    flags = ModelMultipleChoiceField(
        queryset=None, widget=FlagCheckboxSelectMultiple, label=""
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["flags"].initial = self.instance.flags.all().values_list(
            "id", flat=True
        )
        self.fields["flags"].choices = [
            (flag.id, flag)
            for flag in Flag.objects.filter(is_public_beta=True, everyone=False).all()
        ]

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)

        instance.flags.set(self.cleaned_data["flags"])

        return instance
