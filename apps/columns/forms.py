from django import forms
from ibis.expr.datatypes import Date, Floating, Timestamp

from apps.base.core.aggregations import AGGREGATION_TYPE_MAP
from apps.base.core.utils import create_column_choices
from apps.base.forms import BaseLiveSchemaForm
from apps.base.widgets import SelectWithDisable
from apps.columns.models import (
    AddColumn,
    AggregationColumn,
    Column,
    ConvertColumn,
    EditColumn,
    FormulaColumn,
    JoinColumn,
    WindowColumn,
)

from .bigquery import AllOperations, DatePeriod
from .widgets import CodeMirror

IBIS_TO_FUNCTION = {
    "String": "string_function",
    "Int8": "integer_function",
    "Int32": "integer_function",
    "Int64": "integer_function",
    "Float64": "integer_function",
    "Timestamp": "datetime_function",
    "Date": "date_function",
    "Time": "time_function",
    "Boolean": "boolean_function",
}


class ColumnForm(BaseLiveSchemaForm):
    class Meta:
        fields = ("column", "part")
        model = Column

    def get_live_fields(self):
        fields = ["column"]
        if isinstance(self.column_type, (Timestamp, Date)):
            fields += ["part"]
        return fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "part" in self.fields and isinstance(self.column_type, Date):
            self.fields["part"].choices = [
                choice
                for choice in self.fields["part"].choices
                if choice[0] != DatePeriod.DATE.value
            ]


class AggregationColumnForm(BaseLiveSchemaForm):
    class Meta:
        fields = ("column", "function")
        help_texts = {
            "column": "Select the column to aggregate over",
            "function": "Select the aggregation function",
        }
        model = AggregationColumn

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
                for choice in AGGREGATION_TYPE_MAP[self.column_type.name]
            ]


class OperationColumnForm(BaseLiveSchemaForm):
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
        help_texts = {
            "column": "Column",
            "string_function": "Operation",
            "integer_function": "Operation",
            "date_function": "Operation",
            "time_function": "Operation",
            "datetime_function": "Operation",
            "boolean_function": "Operation",
            "integer_value": "Value",
            "float_value": "Value",
            "string_value": "Value",
        }
        widgets = {
            "string_value": forms.Textarea(attrs={"rows": 1}),
        }

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type and (
            function_field := IBIS_TO_FUNCTION[self.column_type.name]
        ):
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


class AddColumnForm(BaseLiveSchemaForm):
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
        help_texts = {
            "column": "Column",
            "string_function": "Operation",
            "integer_function": "Operation",
            "date_function": "Operation",
            "time_function": "Operation",
            "boolean_function": "Operation",
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
        if self.column_type and (
            function_field := IBIS_TO_FUNCTION[self.column_type.name]
        ):
            fields += [function_field]
            operation = AllOperations.get(self.get_live_field(function_field))
            if operation and operation.arguments == 1:
                fields += [operation.value_field]

            if self.get_live_field(function_field) is not None:
                fields += ["label"]

        return fields


class FormulaColumnForm(BaseLiveSchemaForm):
    class Meta:
        fields = ("formula", "label")
        model = FormulaColumn

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["formula"].widget = CodeMirror(self.schema)


class WindowColumnForm(BaseLiveSchemaForm):
    class Meta:
        fields = ("column", "function", "group_by", "order_by", "ascending", "label")
        model = WindowColumn

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = create_column_choices(self.schema)
        self.fields["column"] = forms.ChoiceField(
            choices=choices,
            help_text=self.base_fields["column"].help_text,
        )

        if self.column_type is not None:
            self.fields["function"].choices = [
                (choice.value, choice.name)
                for choice in AGGREGATION_TYPE_MAP[self.column_type.name]
            ]
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

    def get_live_fields(self):
        fields = ["column"]

        if self.column_type is not None:
            fields += ["function", "group_by", "order_by", "ascending", "label"]

        return fields


class ConvertColumnForm(BaseLiveSchemaForm):
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


class JoinColumnForm(BaseLiveSchemaForm):
    class Meta:
        model = JoinColumn
        fields = ["how", "left_column", "right_column"]

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
