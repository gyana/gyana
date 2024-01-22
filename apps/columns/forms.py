from crispy_forms.layout import Layout
from django import forms
from ibis.expr.datatypes import Array, Floating, Struct

from apps.base.core.utils import create_column_choices
from apps.base.forms import ModelForm
from apps.base.widgets import Datalist, SelectWithDisable
from apps.columns.crispy import ColumnFormatting
from apps.columns.models import (
    AddColumn,
    AggregationColumn,
    Column,
    ConvertColumn,
    EditColumn,
    FormulaColumn,
    JoinColumn,
    RenameColumn,
    SortColumn,
    WindowColumn,
)

from .widgets import CodeMirror

IBIS_TO_FUNCTION = {
    "String": "string_function",
    "Int8": "integer_function",
    "Int16": "integer_function",
    "Int32": "integer_function",
    "Int64": "integer_function",
    "Float64": "integer_function",
    "Timestamp": "datetime_function",
    "Date": "date_function",
    "Time": "time_function",
    "Boolean": "boolean_function",
}


def disable_struct_and_array_columns(fields, column_field, schema):
    fields["column"] = forms.ChoiceField(
        choices=column_field.choices,
        help_text=column_field.help_text,
        widget=SelectWithDisable(
            disabled={
                name: "Currently, you cannot use this column type here."
                for name, type_ in schema.items()
                if isinstance(type_, (Struct, Array))
            },
        ),
    )


class ColumnForm(ModelForm):
    class Meta:
        fields = ("column", "part")
        model = Column

        show = {
            "part": "['Date', 'Timestamp'].includes(schema[column])",
        }
        effect = f"choices.part = $store.ibis.date_periods[schema[column]]"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disable_struct_and_array_columns(
            self.fields, self.fields["column"], self.schema
        )


class ColumnFormWithFormatting(ModelForm):
    class Meta:
        model = Column
        fields = (
            "column",
            "part",
            "name",
            "rounding",
            "currency",
            "is_percentage",
            # TODO: support sort implementation for all formsets
            # "sort_index",
            "conditional_formatting",
            "positive_threshold",
            "negative_threshold",
        )
        widgets = {
            "currency": Datalist(),
            # "sort_index": forms.HiddenInput(),
        }
        show = {
            "part": "['Date', 'Timestamp'].includes(schema[column])",
            "rounding": "['Int8', 'Int16', 'Int32', 'Int64', 'Float64'].includes(schema[column])",
            "currency": "['Int8', 'Int16', 'Int32', 'Int64', 'Float64'].includes(schema[column])",
            "is_percentage": "['Int8', 'Int16', 'Int32', 'Int64', 'Float64'].includes(schema[column])",
            "conditional_formatting": "['Int8', 'Int16', 'Int32', 'Int64', 'Float64'].includes(schema[column])",
            "positive_threshold": "['Int8', 'Int16', 'Int32', 'Int64', 'Float64'].includes(schema[column])",
            "negative_threshold": "['Int8', 'Int16', 'Int32', 'Int64', 'Float64'].includes(schema[column])",
        }
        effect = f"choices.part = $store.ibis.date_periods[schema[column]]"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disable_struct_and_array_columns(
            self.fields, self.fields["column"], self.schema
        )

        self.helper.layout = Layout(
            "column",
            "part",
            ColumnFormatting(
                "name",
                [
                    "rounding",
                    "currency",
                    "is_percentage",
                    "conditional_formatting",
                    "positive_threshold",
                    "negative_threshold",
                ],
            ),
        )


class AggregationColumnForm(ModelForm):
    class Meta:
        fields = (
            "column",
            "function",
        )
        help_texts = {
            "column": "Select the column to aggregate over",
            "function": "Select the aggregation function",
        }
        model = AggregationColumn
        show = {"function": "column !== null"}
        effect = f"choices.function = $store.ibis.aggregations[schema[column]]"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disable_struct_and_array_columns(
            self.fields, self.fields["column"], self.schema
        )


class AggregationFormWithFormatting(ModelForm):
    class Meta:
        fields = (
            "column",
            "function",
            "name",
            "rounding",
            "currency",
            "is_percentage",
            # "sort_index",
            "conditional_formatting",
            "positive_threshold",
            "negative_threshold",
        )
        help_texts = {
            "column": "Select the column to aggregate over",
            "function": "Select the aggregation function",
        }
        model = AggregationColumn
        widgets = {
            "currency": Datalist(),
            # "sort_index": forms.HiddenInput(),
        }
        show = {
            "function": "column !== null",
            # TODO: make a decision on how to support this
            # "name": f"kind !== {Widget.Kind.METRIC}",
            # For aggregation column the numeric type of the output is guaranteed
        }
        effect = f"choices.function = $store.ibis.aggregations[schema[column]]"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disable_struct_and_array_columns(
            self.fields, self.fields["column"], self.schema
        )

        self.helper.layout = Layout(
            "column",
            "function",
            ColumnFormatting(
                "name",
                [
                    "rounding",
                    "currency",
                    "is_percentage",
                    "conditional_formatting",
                    "positive_threshold",
                    "negative_threshold",
                ],
            ),
        )


def _show_function_field(field):
    return f"'{field}' == $store.ibis.functions[schema[column]]"


def _show_value_field(field):
    return f"$store.ibis.operations['{field}'].includes($data[computed.function_field])"


class OperationColumnForm(ModelForm):
    class Meta:
        model = EditColumn
        fields = (
            "column",
            "string_function",
            "integer_function",
            "date_function",
            "time_function",
            "boolean_function",
            "datetime_function",
            "integer_value",
            "float_value",
            "string_value",
        )

        widgets = {
            "string_value": forms.Textarea(attrs={"rows": 1}),
        }

        show = {
            k: _show_function_field(k) for k in fields if k.endswith("_function")
        } | {k: _show_value_field(k) for k in fields if k.endswith("_value")}
        effect = f"computed.function_field = $store.ibis.functions[schema[column]]"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disable_struct_and_array_columns(
            self.fields, self.fields["column"], self.schema
        )

    def save(self, commit: bool):
        # Make sure only one function is set and turn the others to Null
        for field in self.base_fields:
            if field.endswith("function") and f"{self.prefix}-{field}" not in self.data:
                setattr(self.instance, field, None)
        return super().save(commit=commit)


class AddColumnForm(ModelForm):
    class Meta:
        model = AddColumn
        fields = (
            "column",
            "string_function",
            "integer_function",
            "date_function",
            "time_function",
            "boolean_function",
            "datetime_function",
            "integer_value",
            "float_value",
            "string_value",
            "label",
        )

        widgets = {
            "string_value": forms.Textarea(attrs={"rows": 1}),
        }

        show = (
            {k: _show_function_field(k) for k in fields if k.endswith("_function")}
            | {k: _show_value_field(k) for k in fields if k.endswith("_value")}
            | {"label": "!!$data[computed.function_field]"}
        )
        effect = f"computed.function_field = $store.ibis.functions[schema[column]]"

    def clean_label(self):
        return column_naming_validation(self.cleaned_data["label"], self.schema.names)


class FormulaColumnForm(ModelForm):
    class Meta:
        fields = ("formula", "label")
        model = FormulaColumn

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["formula"].widget = CodeMirror(self.schema)

    def clean_label(self):
        return column_naming_validation(self.cleaned_data["label"], self.schema.names)


class WindowColumnForm(ModelForm):
    class Meta:
        fields = ("column", "function", "group_by", "order_by", "ascending", "label")
        model = WindowColumn
        show = {
            "function": "column !== null",
            "group_by": "column !== null",
            "order_by": "column !== null",
            "ascending": "column !== null",
            "label": "column !== null",
        }
        effect = f"choices.function = $store.ibis.aggregations[schema[column]]"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        disable_struct_and_array_columns(
            self.fields, self.fields["column"], self.schema
        )
        choices = create_column_choices(self.schema)

        self.fields["group_by"] = forms.ChoiceField(
            choices=choices,
            help_text=self.base_fields["group_by"].help_text,
            required=False,
            widget=SelectWithDisable(
                disabled={
                    name: f"You cannot group by a {type_} column"
                    for name, type_ in self.schema.items()
                    if isinstance(type_, Floating)
                }
            ),
        )
        self.fields["order_by"] = forms.ChoiceField(
            choices=choices,
            help_text=self.base_fields["order_by"].help_text,
            required=False,
        )

    def clean_label(self):
        return column_naming_validation(self.cleaned_data["label"], self.schema.names)


class ConvertColumnForm(ModelForm):
    class Meta:
        fields = ("column", "target_type")
        model = ConvertColumn
        labels = {"target_type": "Type"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["column"].choices = create_column_choices(self.schema)


def create_left_join_choices(parents, index):
    columns = (
        (
            f"Input {idx+1}",
            sorted(
                [(f"{idx}:{col}", col) for col in parent.schema],
                key=lambda x: str.casefold(x[1]),
            ),
        )
        for idx, parent in enumerate(parents[: index + 1])
    )

    return [("", "No column selected"), *columns]


class JoinColumnForm(ModelForm):
    class Meta:
        model = JoinColumn
        fields = ["how", "left_column", "right_column"]

    ignore_live_update_fields = ["how", "left_column", "right_column"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parents = kwargs["parent_instance"].parents_ordered.all()
        index = (
            int(index) if (index := self.prefix.split("-")[-1]) != "__prefix__" else 0
        )

        self.fields["left_column"] = forms.ChoiceField(
            choices=create_left_join_choices(parents, index),
            help_text=self.fields["left_column"].help_text.format(
                index + 1 if index == 0 else f"1 to {index+1}"
            ),
        )
        self.fields["right_column"] = forms.ChoiceField(
            choices=create_column_choices(
                parents[index + 1].schema,
            ),
            help_text=self.fields["right_column"].help_text.format(index + 2),
        )

    def get_initial_for_field(self, field, field_name):
        if field_name == "left_column" and self.instance.left_column:
            return f"{self.instance.left_index}:{self.instance.left_column}"
        return super().get_initial_for_field(field, field_name)

    def save(self, *args, **kwargs):
        left_index, left_column = self.cleaned_data["left_column"].split(":")
        self.instance.left_index = int(left_index)
        self.instance.left_column = left_column

        return super().save(*args, **kwargs)


class SortColumnForm(ModelForm):
    class Meta:
        model = SortColumn
        fields = ["column", "ascending", "sort_index"]
        widgets = {"sort_index": forms.HiddenInput()}


def column_naming_validation(new_name, existing_columns):
    if new_name in (existing_columns):
        raise forms.ValidationError("This column already exists", code="invalid")

    if new_name.lower() in [column.lower() for column in (existing_columns)]:
        raise forms.ValidationError(
            "This column already exists with a different capitalisation", code="invalid"
        )
    return new_name


def extract_values_from_data(prefix, data, field_name, idx=None):
    return tuple(
        value
        for key, value in data.items()
        if key.startswith(prefix)
        and key.endswith(field_name)
        and (idx is None or int(key.split("-")[1]) < idx)
    )


class RenameColumnForm(ModelForm):
    class Meta:
        model = RenameColumn
        fields = ("column", "new_name")

    def clean_new_name(self):
        formset_prefix, idx = self.prefix.split("-")
        idx = int(idx)
        new_names = extract_values_from_data(formset_prefix, self.data, "new_name", idx)
        old_names = extract_values_from_data(formset_prefix, self.data, "column")

        existing_columns = set(self.schema.names) - set(old_names) | set(new_names)
        return column_naming_validation(
            self.cleaned_data["new_name"],
            list(existing_columns),
        )
