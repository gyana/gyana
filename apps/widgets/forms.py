from apps.filters.forms import FilterForm
from apps.filters.models import Filter
from apps.tables.models import Table
from django import forms
from django.forms.models import BaseInlineFormSet

from .models import Widget


class WidgetConfigForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ["table", "kind", "label", "aggregator", "value", "description"]

    def get_live_field(self, name):

        # data populated by POST request in update
        if name in self.data:
            return self.data[name]

        # data populated by GET request in live form
        if name in self.initial:
            return self.initial[name]

        # data populated from database in initial render
        return getattr(self.instance, name, None)

    def get_live_fields(self):

        fields = ["table", "kind", "description"]

        table = self.get_live_field("table")
        kind = self.get_live_field("kind")

        if table and kind and kind != Widget.Kind.TABLE:
            fields += ["label", "aggregator", "value"]

        return fields

    def get_live_formsets(self):
        if self.get_live_field("table") is not None:
            return [FilterFormset]
        return []

    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660
        project = kwargs.pop("project", None)
        schema = kwargs.pop("schema", None)

        super().__init__(*args, **kwargs)

        if project:
            self.fields["table"].queryset = Table.objects.filter(project=project)

        if schema:
            columns = [(column, column) for column in schema]
            self.fields["label"].choices = columns
            self.fields["value"].choices = columns

        live_fields = self.get_live_fields()

        self.fields = {k: v for k, v in self.fields.items() if k in live_fields}

    label = forms.ChoiceField(choices=())
    value = forms.ChoiceField(choices=())


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
