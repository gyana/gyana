from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.base.models import SaveParentModel
from apps.controls.models import DateRange
from apps.widgets.models import Widget


class Filter(SaveParentModel):
    class Type(models.TextChoices):
        INTEGER = "INTEGER", "Integer"
        FLOAT = "FLOAT", "Float"
        STRING = "STRING", "String"
        BOOL = "BOOL", "Bool"
        TIME = "TIME", "Time"
        DATE = "DATE", "Date"
        DATETIME = "DATETIME", "Datetime"
        STRUCT = "STRUCT", "Dictionary"

    class NumericPredicate(models.TextChoices):
        EQUAL = "equal", "is equal to"
        NEQUAL = "nequal", "is not equal to"
        GREATERTHAN = (
            "greaterthan",
            "greater than",
        )
        GREATERTHANEQUAL = "greaterthanequal", "greater than or equal to"
        LESSTHAN = "lessthan", "less than"
        LESSTHANEQUAL = "lessthanequal", "less than or equal"
        ISNULL = "isnull", "is empty"
        NOTNULL = "notnull", "is not empty"
        ISIN = "isin", "is any of"
        NOTIN = "notin", "is none of"

    class StringPredicate(models.TextChoices):
        EQUAL = "equal", "is equal to"
        NEQUAL = "nequal", "is not equal to"
        CONTAINS = "contains", "contains"
        NOTCONTAINS = "notcontains", "does not contain"
        STARTSWITH = "startswith", "starts with"
        ENDSWITH = "endswith", "ends with"
        ISNULL = "isnull", "is empty"
        NOTNULL = "notnull", "is not empty"
        ISIN = "isin", "is any of"
        NOTIN = "notin", "is none of"
        ISUPPERCASE = "isupper", "is uppercase"
        ISLOWERCASE = "islower", "is lowercase"

    class TimePredicate(models.TextChoices):
        ON = "equal", "is"
        NOTON = "nequal", "is not"
        BEFORE = "lessthan", "is before"
        BEFOREON = "lessthanequal", "is on or before"
        AFTER = "greaterthan", "is after"
        AFTERON = "greaterthanequal", "is on or after"
        ISNULL = "isnull", "is empty"
        NOTNULL = "notnull", "is not empty"

    class StructPredicate(models.TextChoices):
        ISNULL = "isnull", "is empty"
        NOTNULL = "notnull", "is not empty"

    widget = models.ForeignKey(
        Widget, on_delete=models.CASCADE, null=True, related_name="filters"
    )
    # Use string reference to avoid circular import
    node = models.ForeignKey(
        "nodes.Node", on_delete=models.CASCADE, related_name="filters", null=True
    )

    column = models.CharField(max_length=300)
    type = models.CharField(max_length=8, choices=Type.choices)

    numeric_predicate = models.CharField(
        max_length=16,
        choices=NumericPredicate.choices,
        null=True,
        verbose_name="Condition",
    )

    float_value = models.FloatField(null=True, verbose_name="Value")
    float_values = ArrayField(models.FloatField(), null=True, verbose_name="Value")
    integer_value = models.BigIntegerField(null=True, verbose_name="Value")
    integer_values = ArrayField(
        models.BigIntegerField(), null=True, verbose_name="Value"
    )

    time_predicate = models.CharField(
        max_length=16,
        choices=TimePredicate.choices,
        null=True,
        verbose_name="Condition",
    )
    datetime_predicate = models.CharField(
        max_length=20,
        choices=TimePredicate.choices + DateRange.choices,
        null=True,
        verbose_name="Condition",
    )

    time_value = models.TimeField(null=True, verbose_name="Value")
    date_value = models.DateField(null=True, verbose_name="Value")
    datetime_value = models.DateTimeField(null=True, verbose_name="Value")

    string_predicate = models.CharField(
        max_length=16,
        choices=StringPredicate.choices,
        null=True,
        verbose_name="Condition",
    )
    string_value = models.TextField(null=True, verbose_name="Value")
    string_values = ArrayField(models.TextField(), null=True, verbose_name="Value")

    bool_value = models.BooleanField(default=True, verbose_name="Value")

    struct_predicate = models.CharField(
        max_length=16,
        choices=StructPredicate.choices,
        null=True,
        verbose_name="Condition",
    )

    def __str__(self):
        return self.column

    @property
    def parent_type(self):
        return "widget" if self.widget else "node"


PREDICATE_MAP = {
    Filter.Type.DATETIME: "datetime_predicate",
    Filter.Type.TIME: "time_predicate",
    Filter.Type.DATE: "datetime_predicate",
    Filter.Type.STRING: "string_predicate",
    Filter.Type.FLOAT: "numeric_predicate",
    Filter.Type.INTEGER: "numeric_predicate",
    Filter.Type.STRUCT: "struct_predicate",
}

NO_VALUE = [
    Filter.NumericPredicate.ISNULL,
    Filter.NumericPredicate.NOTNULL,
    Filter.StringPredicate.ISLOWERCASE,
    Filter.StringPredicate.ISUPPERCASE,
    *DateRange,
]
