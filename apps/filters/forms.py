from django import forms
from django.forms.widgets import Input, TextInput

from apps.base.core.utils import create_column_choices
from apps.base.forms import BaseLiveSchemaForm
from apps.base.widgets import DatetimeInput
from apps.filters.models import NO_VALUE, PREDICATE_MAP, Filter

from .widgets import SelectAutocomplete

IBIS_TO_TYPE = {
    "Int8": Filter.Type.INTEGER,
    "Int32": Filter.Type.INTEGER,
    "Int64": Filter.Type.INTEGER,
    "String": Filter.Type.STRING,
    "Timestamp": Filter.Type.DATETIME,
    "Time": Filter.Type.TIME,
    "Date": Filter.Type.DATE,
    "Float64": Filter.Type.FLOAT,
    "Decimal": Filter.Type.FLOAT,
    "Boolean": Filter.Type.BOOL,
    "Struct": Filter.Type.STRUCT,
}


class FilterForm(BaseLiveSchemaForm):
    column = forms.ChoiceField(choices=[])

    # We have to add the media here because otherwise the form fields
    # Are added dynamically, and a script wouldn't be added if a widget
    # isn't included in the fields
    class Media:
        js = ("js/components-bundle.js",)

    class Meta:
        model = Filter
        fields = (
            "column",
            "string_predicate",
            "numeric_predicate",
            "time_predicate",
            "datetime_predicate",
            "struct_predicate",
            "time_value",
            "date_value",
            "datetime_value",
            "string_value",
            "integer_value",
            "string_values",
            "integer_values",
            "float_value",
            "float_values",
            "bool_predicate",
        )

        widgets = {
            "string_value": TextInput(),
            "datetime_value": DatetimeInput(),
            "date_value": type("DateInput", (Input,), {"input_type": "date"}),
            "time_value": type("TimeInput", (Input,), {"input_type": "time"}),
        }

    def get_live_fields(self):

        fields = ["column"]
        if self.column_type:
            filter_type = IBIS_TO_TYPE[self.column_type.name]
            predicate = PREDICATE_MAP.get(filter_type)
            value = f"{filter_type.lower()}_value"

            # Predicate can be None for booleans
            if predicate:
                fields += [predicate]
                if (
                    pred := self.get_live_field(predicate)
                ) is not None and pred not in NO_VALUE:

                    fields += [value + "s"] if pred in ["isin", "notin"] else [value]

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
            self.fields["column"].choices = create_column_choices(self.schema)

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.column in self.schema:
            instance.type = IBIS_TO_TYPE[self.schema[instance.column].name]

        if commit:
            instance.save()
        return instance
