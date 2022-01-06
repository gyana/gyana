from django.forms.models import ModelMultipleChoiceField

from apps.base.forms import BaseModelForm
from apps.teams.models import Team

from .models import Flag
from .widgets import FlagCheckboxSelectMultiple


class TeamFlagForm(BaseModelForm):
    class Meta:
        model = Team
        fields = ["flags"]

    flags = ModelMultipleChoiceField(
        queryset=None, widget=FlagCheckboxSelectMultiple, label=""
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        flags = self.fields["flags"]
        qs = Flag.objects.filter(is_public_beta=True).exclude(everyone=True).all()

        flags.initial = self.instance.flags.all().values_list("id", flat=True)
        flags.queryset = qs
        flags.choices = [(flag.id, flag) for flag in qs]

    def post_save(self, instance):
        instance.flags.set(self.cleaned_data["flags"])
