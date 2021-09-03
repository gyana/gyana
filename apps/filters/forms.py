from apps.base.live_update_form import LiveUpdateForm
from apps.base.schema_form_mixin import SchemaFormMixin
from apps.filters.models import PREDICATE_MAP, Filter
from django import forms
from django.forms.widgets import Input, TextInput

from .widgets import DatetimeInput, SelectAutocomplete

IBIS_TO_TYPE = {
    "Int64": Filter.Type.INTEGER,
    "String": Filter.Type.STRING,
    "Timestamp": Filter.Type.DATETIME,
    "Time": Filter.Type.TIME,
    "Date": Filter.Type.DATE,
    "Float64": Filter.Type.FLOAT,
    "Boolean": Filter.Type.BOOL,
}


class FilterForm(SchemaFormMixin, LiveUpdateForm):
    column = forms.ChoiceField(choices=[], help_text="Column")

    # We have to add the media here because otherwise the form fields
    # Are added dynamically, and a script wouldn't be added if a widget
    # isn't included in the fields
    class Media:
        js = ("js/components-bundle.js",)

    class Meta:
        fields = (
            "column",
            "string_predicate",
            "numeric_predicate",
            "time_predicate",
            "datetime_predicate",
            "time_value",
            "date_value",
            "datetime_value",
            "string_value",
            "integer_value",
            "string_values",
            "integer_values",
            "float_value",
            "float_values",
            "bool_value",
        )
        help_texts = {
            "string_predicate": "Condition",
            "string_predicate": "Condition",
            "numeric_predicate": "Condition",
            "time_predicate": "Condition",
            "datetime_predicate": "Condition",
            "time_value": "Value",
            "date_value": "Value",
            "datetime_value": "Value",
            "string_value": "Value",
            "integer_value": "Value",
            "string_values": "Value",
            "integer_values": "Value",
            "float_value": "Value",
            "float_values": "Value",
            "bool_value": "Value",
        }
        widgets = {
            "string_value": TextInput(),
            "datetime_value": DatetimeInput(),
            "date_value": type("DateInput", (Input,), {"input_type": "date"}),
            "time_value": type("TimeInput", (Input,), {"input_type": "time"}),
        }

    def get_live_fields(self):

        fields = ["column"]
        if self.column_type:
            filter_type = IBIS_TO_TYPE[self.column_type]
            predicate = PREDICATE_MAP.get(filter_type)
            value = f"{filter_type.lower()}_value"

            # Predicate can be None for booleans
            if predicate:
                fields += [predicate]
                if (
                    pred := self.get_live_field(predicate)
                ) is not None and pred not in [
                    "isnull",
                    "notnull",
                    "isupper",
                    "islower",
                    "today",
                    "tomorrow",
                    "yesterday",
                ]:

                    if pred in ["isin", "notin"]:
                        fields += [value + "s"]
                    else:
                        fields += [value]

            if filter_type == Filter.Type.BOOL:
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
