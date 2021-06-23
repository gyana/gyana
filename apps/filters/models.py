from apps.widgets.models import Widget
from dirtyfields import DirtyFieldsMixin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from model_clone import CloneMixin


class Filter(CloneMixin, DirtyFieldsMixin, models.Model):
    class Type(models.TextChoices):
        INTEGER = "INTEGER", "Integer"
        FLOAT = "FLOAT", "Float"
        STRING = "STRING", "String"
        BOOL = "BOOL", "Bool"
        TIME = "TIME", "Time"
        DATE = "DATE", "Date"
        DATETIME = "DATETIME", "Datetime"

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
        BEFORE = "greaterthan", "is before"
        BEFOREON = "greaterthanequal", "is on or before"
        AFTER = "lessthan", "is after"
        AFTERON = "lessthanequal", "is on or after"
        ISNULL = "isnull", "is empty"
        NOTNULL = "notnull", "is not empty"

    class DatetimePredicate(models.TextChoices):
        TODAY = "today", "today"
        TOMORROW = "tomorrow", "tomorrow"
        YESTERDAY = "yesterday", "yesterday"
        ONEWEEKAGO = "oneweekago", "one week ago"
        ONEMONTHAGO = "onemonthago", "one month ago"
        ONEYEARAGO = "oneyearago", "one year ago"

    widget = models.ForeignKey(
        Widget, on_delete=models.CASCADE, null=True, related_name="filters"
    )
    # Use string reference to avoid circular import
    node = models.ForeignKey(
        "workflows.Node", on_delete=models.CASCADE, related_name="filters", null=True
    )

    column = models.CharField(max_length=300)
    type = models.CharField(max_length=8, choices=Type.choices)

    numeric_predicate = models.CharField(
        max_length=16, choices=NumericPredicate.choices, null=True, blank=True
    )

    float_value = models.FloatField(null=True, blank=True)
    float_values = ArrayField(models.FloatField(), null=True)
    integer_value = models.BigIntegerField(null=True, blank=True)
    integer_values = ArrayField(models.BigIntegerField(), null=True)

    time_predicate = models.CharField(
        max_length=16, choices=TimePredicate.choices, null=True, blank=True
    )
    datetime_predicate = models.CharField(
        max_length=16,
        choices=TimePredicate.choices + DatetimePredicate.choices,
        null=True,
        blank=True,
    )

    time_value = models.TimeField(null=True, blank=True)
    date_value = models.DateField(null=True, blank=True)
    datetime_value = models.DateTimeField(null=True, blank=True)

    string_predicate = models.CharField(
        max_length=16, choices=StringPredicate.choices, null=True, blank=True
    )
    string_value = models.TextField(null=True, blank=True)
    string_values = ArrayField(models.TextField(), null=True)

    bool_value = models.BooleanField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.column

    @property
    def parent_type(self):
        return "widget" if self.widget else "node"

    @property
    def parent(self):
        return self.widget or self.node

    def save(self, *args, **kwargs) -> None:
        if self.node and self.is_dirty():
            self.node.updated = timezone.now()
            self.node.save()

        return super().save(*args, **kwargs)


PREDICATE_MAP = {
    Filter.Type.DATETIME: "datetime_predicate",
    Filter.Type.TIME: "time_predicate",
    Filter.Type.DATE: "datetime_predicate",
    Filter.Type.STRING: "string_predicate",
    Filter.Type.FLOAT: "numeric_predicate",
    Filter.Type.INTEGER: "numeric_predicate",
}
