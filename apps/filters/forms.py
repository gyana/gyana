from apps.utils.live_update_form import LiveUpdateForm
from django import forms
from django.forms.widgets import TextInput

IBIS_TO_TYPE = {"Int64": "INTEGER", "String": "STRING"}


class FilterForm(LiveUpdateForm):
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

        column = self.get_live_field("column")
        column_type = None
        if self.schema and column in self.schema:
            column_type = self.schema[column].name

        if column_type == "String":
            fields += ["string_predicate", "string_value"]
        elif column_type == "Int64":
            fields += ["numeric_predicate", "integer_value"]

        return fields

    def __init__(self, *args, **kwargs):

        self.schema = kwargs.pop("schema", None)

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
