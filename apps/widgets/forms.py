from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from apps.tables.models import Table
from django import forms
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import HiddenInput

from .models import Widget


class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ["name", "dashboard", "table", "visual_kind"]
        widgets = {"dashboard": HiddenInput()}

    def get_formsets(self):
        if (
            self.data.get("table") or self.initial.get("table") or self.instance.table
        ) is not None:
            return [FilterFormset]
        return []

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields["table"].queryset = Table.objects.filter(project=project)


class InlineFilterFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.form.base_fields["column"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.parents.first().schema],
            ]
        )


FilterFormset = forms.inlineformset_factory(
    Widget,
    Filter,
    form=FilterForm,
    can_delete=True,
    extra=1,
    # formset=InlineFilterFormset,
)


class WidgetConfigForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ["kind", "aggregator", "label", "value"]

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        self.columns = kwargs.pop("columns")
        super().__init__(*args, **kwargs)
        self.fields["label"].choices = self.columns
        self.fields["value"].choices = self.columns

    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())
