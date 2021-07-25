from apps.nodes.models import AggregationFunctions, Node
from apps.utils.models import BaseModel
from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from model_clone import CloneMixin

from .bigquery import (
    CommonOperations,
    DateOperations,
    DatetimeOperations,
    NumericOperations,
    StringOperations,
    TimeOperations,
)

bigquery_column_regex = RegexValidator(
    r"^[a-zA-Z_][0-9a-zA-Z_]*$", "Only numbers, letters and underscores allowed."
)


class SaveParentModel(DirtyFieldsMixin, CloneMixin, BaseModel):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        if self.is_dirty():
            self.node.data_updated = timezone.now()
            self.node.save()
        return super().save(*args, **kwargs)


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
    )
    integer_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **NumericOperations}.items()
        ),
        null=True,
    )
    date_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **DateOperations}.items()
        ),
        null=True,
    )
    time_function = models.CharField(
        max_length=20,
        choices=(
            (key, value.label)
            for key, value in {**CommonOperations, **TimeOperations}.items()
        ),
        null=True,
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
    )

    integer_value = models.BigIntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    string_value = models.TextField(null=True, blank=True)

    @property
    def function(self):
        return (
            self.string_function
            or self.integer_function
            or self.date_function
            or self.time_function
            or self.datetime_function
        )


class Column(SaveParentModel):
    column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, help_text="Select columns"
    )
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="columns")


class SecondaryColumn(SaveParentModel):
    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="secondary_columns"
    )


class FunctionColumn(SaveParentModel):

    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    function = models.CharField(max_length=20, choices=AggregationFunctions.choices)
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="aggregations"
    )


class SortColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="sort_columns"
    )
    ascending = models.BooleanField(
        default=True, help_text="Select to sort ascendingly"
    )
    column = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        help_text="Select column to sort on",
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
    )


class RenameColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="rename_columns"
    )
    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    new_name = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
    )


class FormulaColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="formula_columns"
    )
    formula = models.TextField(null=True, blank=True)
    label = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
    )


class WindowColumn(SaveParentModel):
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="window_columns"
    )

    column = models.CharField(max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH)
    function = models.CharField(max_length=20, choices=AggregationFunctions.choices)
    group_by = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    order_by = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH, null=True, blank=True
    )
    ascending = models.BooleanField(
        default=True, help_text="Select to sort ascendingly"
    )
    label = models.CharField(
        max_length=settings.BIGQUERY_COLUMN_NAME_LENGTH,
        validators=[bigquery_column_regex],
    )
