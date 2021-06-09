from apps.utils.live_update_form import LiveUpdateForm
from apps.utils.schema_form_mixin import SchemaFormMixin
from django import forms
from django.forms.widgets import TextInput

from .widgets import SelectAutocomplete

IBIS_TO_TYPE = {"Int64": "INTEGER", "String": "STRING"}


class FilterForm(SchemaFormMixin, LiveUpdateForm):
    column = forms.ChoiceField(choices=[])

    # We have to add the media here because otherwise the form fields
    # Are added dynamically, and a script wouldn't be added if a widget
    # isn't included in the fields
    class Media:
        js = ("js/templates-bundle.js",)

    class Meta:
        fields = (
            "column",
            "string_predicate",
            "numeric_predicate",
            "string_value",
            "integer_value",
            "string_values",
            "integer_values",
        )
        widgets = {"string_value": TextInput()}

    def get_live_fields(self):

        fields = ["column"]
        predicate = None
        if self.column_type == "String":
            predicate = "string_predicate"
            value = "string_value"
            fields += [predicate]
        elif self.column_type == "Int64":
            predicate = "numeric_predicate"
            value = "integer_value"
            fields += ["numeric_predicate"]

        if (
            self.column_type
            and predicate
            and (pred := self.get_live_field(predicate)) is not None
            and pred
            not in [
                "isnull",
                "notnull",
            ]
        ):
            if pred in ["isin", "notin"]:
                fields += [value + "s"]
            else:
                fields += [value]

        return fields

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # We add the widgets for the array values here because
        # We need to initialize them with some run-time configurations
        field = list(filter(lambda x: x.endswith("_values"), self.fields.keys()))
        if field:
            self.fields[field[0]].widget = SelectAutocomplete(
                None, instance=self.instance, column=self.get_live_field("column")
            )

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
