from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.base.models import SaveParentModel
from apps.widgets.models import Widget


class DateRange(models.TextChoices):
    TODAY = "today", "today"
    TOMORROW = "tomorrow", "tomorrow"
    YESTERDAY = "yesterday", "yesterday"
    ONEWEEKAGO = "oneweekago", "one week ago"
    ONEMONTHAGO = "onemonthago", "one month ago"
    ONEYEARAGO = "oneyearago", "one year ago"
    THIS_WEEK = "thisweek", "This week (starts Monday)"
    THIS_WEEK_UP_TO_DATE = "thisweekuptodate", "This week (starts Monday) up to date"
    LAST_WEEK = "lastweek", "Last week (starts Monday)"
    LAST_7 = "last7", "Last 7 days"
    LAST_14 = "last14", "Last 14 days"
    LAST_28 = "last28", "Last 28 days"
    THIS_MONTH = "thismonth", "This month"
    THIS_MONTH_UP_TO_DATE = "thismonthuptodate", "This month to date"
    LAST_MONTH = "lastmonth", "Last month"
    LAST_30 = "last30", "Last 30 days"
    LAST_90 = "last90", "Last 90 days"
    THIS_QUARTER = "thisquarter", "This quarter"
    THIS_QUARTER_UP_TO_DATE = "thisquarteruptodate", "This quarter up to date"
    LAST_QUARTER = "lastquarter", "Last quarter"
    LAST_180 = "last180", "Last 180 days"
    LAST_12_MONTH = "last12month", "Last 12 months"
    LAST_YEAR = "lastyear", "Last calendar year"
    THIS_YEAR = "thisyear", "This year"
    THIS_YEAR_UP_TO_DATE = "thisyearuptodate", "This year (January - up to date)"


class Filter(SaveParentModel):
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
        BEFORE = "lessthan", "is before"
        BEFOREON = "lessthanequal", "is on or before"
        AFTER = "greaterthan", "is after"
        AFTERON = "greaterthanequal", "is on or after"
        ISNULL = "isnull", "is empty"
        NOTNULL = "notnull", "is not empty"

    widget = models.ForeignKey(
        Widget, on_delete=models.CASCADE, null=True, related_name="filters"
    )
    # Use string reference to avoid circular import
    node = models.ForeignKey(
        "nodes.Node", on_delete=models.CASCADE, related_name="filters", null=True
    )

    column = models.CharField(max_length=300, help_text="Column")
    type = models.CharField(max_length=8, choices=Type.choices)

    numeric_predicate = models.CharField(
        max_length=16, choices=NumericPredicate.choices, null=True
    )

    float_value = models.FloatField(null=True)
    float_values = ArrayField(models.FloatField(), null=True)
    integer_value = models.BigIntegerField(null=True)
    integer_values = ArrayField(models.BigIntegerField(), null=True)

    time_predicate = models.CharField(
        max_length=16, choices=TimePredicate.choices, null=True
    )
    datetime_predicate = models.CharField(
        max_length=20,
        choices=TimePredicate.choices + DateRange.choices,
        null=True,
    )

    time_value = models.TimeField(null=True)
    date_value = models.DateField(null=True)
    datetime_value = models.DateTimeField(null=True)

    string_predicate = models.CharField(
        max_length=16, choices=StringPredicate.choices, null=True
    )
    string_value = models.TextField(null=True)
    string_values = ArrayField(models.TextField(), null=True)

    bool_value = models.BooleanField(default=True)

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
}

NO_VALUE = [
    Filter.NumericPredicate.ISNULL,
    Filter.NumericPredicate.NOTNULL,
    Filter.StringPredicate.ISLOWERCASE,
    Filter.StringPredicate.ISUPPERCASE,
    *DateRange,
]
