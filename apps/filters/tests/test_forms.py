import pytest
from django.http import QueryDict

from apps.base.tests.asserts import assertFormChoicesLength
from apps.base.tests.mock_data import TABLE
from apps.filters.forms import FilterForm
from apps.filters.models import DateRange, Filter

pytestmark = pytest.mark.django_db

COLUMN_LENGTH = 9
NUMERIC_LENGTH = 11
STRING_LENGTH = 13
TIME_LENGTH = 9
DATETIME_LENGTH = 35

NUMERIC_NO_VALUE = [Filter.NumericPredicate.ISNULL, Filter.NumericPredicate.NOTNULL]
STRING_NO_VALUE = [
    Filter.StringPredicate.ISNULL,
    Filter.StringPredicate.NOTNULL,
    Filter.StringPredicate.ISUPPERCASE,
    Filter.StringPredicate.ISLOWERCASE,
]
TIME_NO_VALUE = [Filter.TimePredicate.ISNULL, Filter.TimePredicate.NOTNULL]
DATETIME_NO_VALUE = TIME_NO_VALUE + [
    DateRange.TODAY,
    DateRange.TOMORROW,
    DateRange.YESTERDAY,
    DateRange.ONEMONTHAGO,
    DateRange.ONEWEEKAGO,
    DateRange.ONEYEARAGO,
    DateRange.THIS_WEEK,
    DateRange.LAST_WEEK,
    DateRange.LAST_7,
    DateRange.LAST_14,
    DateRange.LAST_28,
    DateRange.THIS_MONTH,
    DateRange.LAST_MONTH,
    DateRange.LAST_30,
    DateRange.LAST_90,
    DateRange.THIS_QUARTER,
    DateRange.LAST_QUARTER,
    DateRange.LAST_180,
    DateRange.LAST_12_MONTH,
    DateRange.LAST_YEAR,
    DateRange.THIS_YEAR,
]

NUMERIC_VALUE = [
    Filter.NumericPredicate.EQUAL,
    Filter.NumericPredicate.NEQUAL,
    Filter.NumericPredicate.GREATERTHAN,
    Filter.NumericPredicate.GREATERTHANEQUAL,
    Filter.NumericPredicate.LESSTHAN,
    Filter.NumericPredicate.LESSTHANEQUAL,
]
NUMERIC_VALUES = [Filter.NumericPredicate.ISIN, Filter.NumericPredicate.NOTIN]
STRING_VALUE = [
    Filter.StringPredicate.EQUAL,
    Filter.StringPredicate.NEQUAL,
    Filter.StringPredicate.CONTAINS,
    Filter.StringPredicate.NOTCONTAINS,
    Filter.StringPredicate.STARTSWITH,
    Filter.StringPredicate.ENDSWITH,
]
STRING_VALUES = [Filter.StringPredicate.ISIN, Filter.StringPredicate.NOTIN]
TIME_VALUE = [
    Filter.TimePredicate.ON,
    Filter.TimePredicate.NOTON,
    Filter.TimePredicate.BEFORE,
    Filter.TimePredicate.BEFOREON,
    Filter.TimePredicate.AFTER,
    Filter.TimePredicate.AFTERON,
]


def parametrize_column_predicate(
    column, column_type, predicate_name, predicate_length, predicates, value_name=None
):
    return [
        pytest.param(
            {"column": column, predicate_name: predicate},
            {"column", predicate_name} | ({value_name} if value_name else set()),
            {"column": COLUMN_LENGTH, predicate_name: predicate_length},
            id=f"{column_type} column with {predicate}",
        )
        for predicate in predicates
    ]


@pytest.mark.parametrize(
    "data, expected_fields, choice_lengths",
    [
        pytest.param(
            {},
            {"column"},
            {"column": COLUMN_LENGTH},
            id="empty form",
        ),
        pytest.param(
            {"column": "id"},
            {"column", "numeric_predicate"},
            {"column": COLUMN_LENGTH, "numeric_predicate": NUMERIC_LENGTH},
            id="integer column",
        ),
        *parametrize_column_predicate(
            "id", "integer", "numeric_predicate", NUMERIC_LENGTH, NUMERIC_NO_VALUE
        ),
        *parametrize_column_predicate(
            "stars", "float", "numeric_predicate", NUMERIC_LENGTH, NUMERIC_NO_VALUE
        ),
        *parametrize_column_predicate(
            "athlete", "string", "string_predicate", STRING_LENGTH, STRING_NO_VALUE
        ),
        *parametrize_column_predicate(
            "lunch", "time", "time_predicate", TIME_LENGTH, TIME_NO_VALUE
        ),
        *parametrize_column_predicate(
            "birthday", "date", "datetime_predicate", DATETIME_LENGTH, DATETIME_NO_VALUE
        ),
        *parametrize_column_predicate(
            "when",
            "datetime",
            "datetime_predicate",
            DATETIME_LENGTH,
            DATETIME_NO_VALUE,
        ),
        *parametrize_column_predicate(
            "id",
            "integer",
            "numeric_predicate",
            NUMERIC_LENGTH,
            NUMERIC_VALUE,
            "integer_value",
        ),
        *parametrize_column_predicate(
            "stars",
            "float",
            "numeric_predicate",
            NUMERIC_LENGTH,
            NUMERIC_VALUE,
            "float_value",
        ),
        *parametrize_column_predicate(
            "id",
            "integer",
            "numeric_predicate",
            NUMERIC_LENGTH,
            NUMERIC_VALUES,
            "integer_values",
        ),
        *parametrize_column_predicate(
            "stars",
            "float",
            "numeric_predicate",
            NUMERIC_LENGTH,
            NUMERIC_VALUES,
            "float_values",
        ),
        *parametrize_column_predicate(
            "athlete",
            "string",
            "string_predicate",
            STRING_LENGTH,
            STRING_VALUE,
            "string_value",
        ),
        *parametrize_column_predicate(
            "athlete",
            "string",
            "string_predicate",
            STRING_LENGTH,
            STRING_VALUES,
            "string_values",
        ),
        *parametrize_column_predicate(
            "lunch",
            "time",
            "time_predicate",
            TIME_LENGTH,
            TIME_VALUE,
            "time_value",
        ),
        *parametrize_column_predicate(
            "when",
            "datetime",
            "datetime_predicate",
            DATETIME_LENGTH,
            TIME_VALUE,
            "datetime_value",
        ),
        *parametrize_column_predicate(
            "birthday",
            "datetime",
            "datetime_predicate",
            DATETIME_LENGTH,
            TIME_VALUE,
            "date_value",
        ),
        pytest.param(
            {"column": "is_nice"},
            {"column", "bool_value"},
            {},
            id="bool column",
        ),
    ],
)
def test_filter_form(
    data, expected_fields, choice_lengths, filter_factory, node_factory
):
    filter_ = filter_factory(node=node_factory())
    query_dict = QueryDict(mutable=True)
    query_dict.update(data)
    form = FilterForm(instance=filter_, schema=TABLE.schema(), data=query_dict)

    assert set(form.fields.keys()) == expected_fields

    for field, length in choice_lengths.items():
        assertFormChoicesLength(form, field, length)
