from apps.base.aggregations import AGGREGATION_TYPE_MAP
from apps.base.live_update_form import LiveUpdateForm
from apps.base.schema_form_mixin import SchemaFormMixin
from django import forms
from django.forms.models import BaseInlineFormSet

from .bigquery import AllOperations
from .widgets import CodeMirror

IBIS_TO_FUNCTION = {
    "String": "string_function",
    "Int64": "integer_function",
    "Float64": "integer_function",
    "Timestamp": "datetime_function",
    "Date": "date_function",
    "Time": "time_function",
}


class InlineColumnFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.form.base_fields["column"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.parents.first().schema],
            ]
        )


class FunctionColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = ("column", "function")

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type is not None:
            fields += ["function"]

        return fields

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.column_type is not None:
            self.fields["function"].choices = [
                (choice.value, choice.name)
                for choice in AGGREGATION_TYPE_MAP[self.column_type]
            ]


class OperationColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = (
            "column",
            "string_function",
            "integer_function",
            "date_function",
            "time_function",
            "datetime_function",
            "integer_value",
            "float_value",
            "string_value",
        )
        help_texts = {
            "column": "Column",
            "string_function": "Operation",
            "integer_function": "Operation",
            "date_function": "Operation",
            "time_function": "Operation",
            "datetime_function": "Operation",
        }
        widgets = {
            "string_value": forms.Textarea(attrs={"rows": 1}),
        }

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type and (function_field := IBIS_TO_FUNCTION[self.column_type]):
            fields += [function_field]
            operation = AllOperations.get(self.get_live_field(function_field))
            if operation and operation.arguments == 1:
                fields += [operation.value_field]

        return fields

    def save(self, commit: bool):
        # Make sure only one function is set and turn the others to Null
        for field in self.base_fields:
            if field.endswith("function") and f"{self.prefix}-{field}" not in self.data:
                setattr(self.instance, field, None)
        return super().save(commit=commit)


class AddColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = (
            "column",
            "string_function",
            "integer_function",
            "date_function",
            "time_function",
            "datetime_function",
            "integer_value",
            "float_value",
            "string_value",
            "label",
        )
        help_texts = {
            "column": "Column",
            "string_function": "Operation",
            "integer_function": "Operation",
            "date_function": "Operation",
            "time_function": "Operation",
            "datetime_function": "Operation",
            "integer_value": "Value",
            "float_value": "Value",
            "string_value": "Value",
            "label": "New Column Name",
        }
        widgets = {
            "string_value": forms.Textarea(attrs={"rows": 1}),
        }

    def get_live_fields(self):
        fields = ["column"]
        if self.column_type and (function_field := IBIS_TO_FUNCTION[self.column_type]):
            fields += [function_field]
            operation = AllOperations.get(self.get_live_field(function_field))
            if operation and operation.arguments == 1:
                fields += [operation.value_field]

            if self.get_live_field(function_field) is not None:
                fields += ["label"]

        return fields


class FormulaColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = ("formula", "label")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["formula"].widget = CodeMirror(self.schema)


class WindowColumnForm(SchemaFormMixin, LiveUpdateForm):
    class Meta:
        fields = ("column", "function", "group_by", "order_by", "ascending", "label")
        help_texts = {
            "column": "Column",
            "function": "Function",
            "group_by": "Group By",
            "order_by": "Order By",
            "label": "New Column Name",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        column_field = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.schema],
            ]
        )
        self.fields["column"] = column_field
        if self.column_type is not None:
            self.fields["function"].choices = [
                (choice.value, choice.name)
                for choice in AGGREGATION_TYPE_MAP[self.column_type]
            ]
            self.fields["group_by"] = column_field
            self.fields["order_by"] = column_field

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type is not None:
            fields += ["function", "group_by", "order_by", "ascending", "label"]

        return fields
