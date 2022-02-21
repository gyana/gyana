from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from apps.base.core.aggregations import AggregationFunctions
from apps.base.models import SaveParentModel
from apps.columns.currency_symbols import CurrencySymbols
from apps.nodes.models import Node

from .bigquery import (
    CommonOperations,
    DateOperations,
    DatePeriod,
    DatetimeOperations,
    NumericOperations,
    StringOperations,
    TimeOperations,
)

bigquery_column_regex = RegexValidator(
    r"^[a-zA-Z_][0-9a-zA-Z_]*$", "Only numbers, letters and underscores allowed."
)


class AbstractOperationColumn(SaveParentModel):
    class Meta:
        abstract = True

    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)

    string_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **StringOperations}.items()
        ),
        null=True,
        verbose_name="Operation",
    )
    integer_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **NumericOperations}.items()
        ),
        null=True,
        verbose_name="Operation",
    )
    date_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **DateOperations}.items()
        ),
        null=True,
        verbose_name="Operation",
    )
    time_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **TimeOperations}.items()
        ),
        null=True,
        verbose_name="Operation",
    )
    datetime_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {
                **CommonOperations,
                **TimeOperations,
                **DateOperations,
                **DatetimeOperations,
            }.items()
        ),
        null=True,
        verbose_name="Operation",
    )

    boolean_function = models.CharField(
        max_length=20,
        choices=((key, value.label) for key, value in {**CommonOperations}.items()),
        null=True,
        verbose_name="Operation",
    )

    integer_value = models.BigIntegerField(null=True, verbose_name="Value")
    float_value = models.FloatField(null=True, verbose_name="Value")
    string_value = models.TextField(null=True, verbose_name="Value")

    @property
    def function(self):
        return (
            self.string_function
            or self.integer_function
            or self.date_function
            or self.time_function
            or self.datetime_function
        )


class ColumnSettings(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Set column header name",
    )
    rounding = models.IntegerField(default=2, help_text="Decimal point to round to")
    currency = models.CharField(
        max_length=32,
        choices=CurrencySymbols.choices,
        blank=True,
        null=True,
        help_text="Select a currency",
    )
    is_percentage = models.BooleanField(
        default=False, blank=True, verbose_name="Show in %"
    )


class Column(ColumnSettings, SaveParentModel):
    column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, help_text="Select columns"
    )
    node = models.ForeignKey(
        Node, null=True, on_delete=models.CASCADE, related_name="columns"
    )
    widget = models.ForeignKey(
        "widgets.Widget", on_delete=models.CASCADE, related_name="columns", null=True
    )
    part = models.CharField(
        max_length=16,
        choices=DatePeriod.choices,
        null=True,
        blank=True,
        help_text="Select the desired date part",
    )


class ConvertColumn(SaveParentModel):
    class TargetTypes(models.TextChoices):
        TEXT = "text", "Text"
        INT = "int", "Integer"
        FLOAT = "float", "Decimal"
        BOOL = "bool", "Bool"
        DATE = "date", "Date"
        TIME = "time", "Time"
        DATETIME = "timestamp", "Datetime"

    column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, help_text="Select column"
    )
    target_type = models.CharField(
        max_length=16,
        choices=TargetTypes.choices,
        help_text="Select type to convert to",
    )
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="convert_columns"
    )


class SecondaryColumn(SaveParentModel):
    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="secondary_columns"
    )


class AggregationColumn(ColumnSettings, SaveParentModel):
    class Meta:
        ordering = ("created",)

    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    function = models.CharField(max_length=20, choices=AggregationFunctions.choices)
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="aggregations", null=True
    )
    widget = models.ForeignKey(
        "widgets.Widget",
        on_delete=models.CASCADE,
        related_name="aggregations",
        null=True,
    )


class SortColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="sort_columns"
    )
    ascending = models.BooleanField(default=True, help_text="Ascending Sort")
    column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
    )


class EditColumn(AbstractOperationColumn):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="edit_columns"
    )


class AddColumn(AbstractOperationColumn):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="add_columns")
    label = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
        verbose_name="New column name",
    )


class RenameColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="rename_columns"
    )
    column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, verbose_name="Old column name"
    )
    new_name = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
        verbose_name="New column name",
    )


class FormulaColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="formula_columns"
    )
    formula = models.TextField(null=True, help_text="Type formula")
    label = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
        help_text="New column name",
    )


class WindowColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="window_columns"
    )

    column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        help_text="Choose an aggregation column",
    )
    function = models.CharField(
        max_length=20,
        choices=AggregationFunctions.choices,
        help_text="Select an aggregation function",
    )
    group_by = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="Group over this column",
    )
    order_by = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        null=True,
        blank=True,
        help_text="Order by this column",
    )
    ascending = models.BooleanField(
        default=True, help_text="Select to sort ascendingly"
    )
    label = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
        help_text="Select a new column name",
    )


class JoinColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="join_columns"
    )
    how = models.CharField(
        max_length=12,
        choices=[
            ("inner", "Inner"),
            ("outer", "Outer"),
            ("left", "Left"),
            ("right", "Right"),
        ],
        default="inner",
        help_text="Select the join method, more information in the docs",
    )

    left_index = models.IntegerField(default=0)
    left_column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        help_text="Choose the join column from Input {}",
    )

    right_column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        help_text="Choose the right join column from Input {}",
    )
