from apps.utils.live_update_form import LiveUpdateForm
from apps.utils.schema_form_mixin import SchemaFormMixin
from django import forms
from django.forms.widgets import TextInput

IBIS_TO_TYPE = {"Int64": "INTEGER", "String": "STRING"}


class FilterForm(SchemaFormMixin, LiveUpdateForm):
    column = forms.ChoiceField(choices=[])

    class Meta:
        fields = (
            "column",
            "string_predicate",
            "numeric_predicate",
            "string_value",
            "integer_value",
        )
        widgets = {"string_value": TextInput()}

    def get_live_fields(self):

        fields = ["column"]

        if self.column_type == "String":
            fields += ["string_predicate", "string_value"]
        elif self.column_type == "Int64":
            fields += ["numeric_predicate", "integer_value"]

        return fields

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.schema:
            self.fields["column"].choices = [
                ("", "No column selected"),
            ] + [(col, col) for col in self.schema]

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.column in self.schema:
            instance.type = IBIS_TO_TYPE[self.schema[instance.column].name]

        if commit:
            instance.save()
        return instance
