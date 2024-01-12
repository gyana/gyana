from django import forms
from django.forms.widgets import Input, TextInput

from apps.base.core.utils import create_column_choices
from apps.base.forms import LiveAlpineModelForm, SchemaFormMixin
from apps.base.widgets import DatetimeInput
from apps.filters.models import NO_VALUE, PREDICATE_MAP, Filter

from .widgets import SelectAutocomplete

IBIS_TO_TYPE = {
    "Int8": Filter.Type.INTEGER,
    "Int16": Filter.Type.INTEGER,
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

TYPE_TO_IBIS = {
    Filter.Type.INTEGER: ["Int8", "Int16", "Int32", "Int64"],
    Filter.Type.STRING: ["String"],
    Filter.Type.DATETIME: ["Timestamp"],
    Filter.Type.TIME: ["Time"],
    Filter.Type.DATE: ["Date"],
    Filter.Type.FLOAT: ["Float64", "Decimal"],
    Filter.Type.BOOL: ["Boolean"],
    Filter.Type.STRUCT: ["Struct"],
}


def _get_show_for_predicate(predicate):
    filter_types = [
        k for k, v in PREDICATE_MAP.items() if v == f"{predicate}_predicate"
    ]
    ibis = [y for x in filter_types for y in TYPE_TO_IBIS[x]]
    return f"{ibis}.includes(schema[column])"


def _get_show_for_value(filter_type, multiple=False):
    predicate = PREDICATE_MAP[filter_type]
    ibis = TYPE_TO_IBIS[filter_type]
    no_value = [x.value for x in NO_VALUE]

    is_ibis = f"{ibis}.includes(schema[column])"
    is_predicate = f"({predicate} !== null) && !{no_value}.includes({predicate})"
    is_multiple = f"['isin', 'notin'].includes({predicate})"

    # TODO: clarify this comment
    # Predicate can be None for booleans

    if multiple:
        return f"{is_ibis} && {is_predicate} && {is_multiple}"

    return f"{is_ibis} && {is_predicate} && !{is_multiple}"


class FilterForm(SchemaFormMixin, LiveAlpineModelForm):
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

        show = (
            {
                f"{p}_predicate": _get_show_for_predicate(p)
                for p in ["string", "numeric", "time", "datetime", "struct", "bool"]
            }
            | {f"{f.lower()}_value": _get_show_for_value(f) for f in Filter.Type}
            | {
                f"{f.lower()}_values": _get_show_for_value(f, multiple=True)
                for f in [Filter.Type.INTEGER, Filter.Type.STRING, Filter.Type.FLOAT]
            }
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # We add the widgets for the array values here because
        # We need to initialize them with some run-time configurations
        for field in [k for k in self.fields if k.endswith("_values")]:
            self.fields[field].widget = SelectAutocomplete(
                None,
                parent_type=self.parent_instance._meta.model_name,
                parent_id=self.parent_instance.id,
                selected=getattr(self.instance, field) or [],
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
