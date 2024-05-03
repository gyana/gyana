import pytest

from apps.filters.engine import get_query_from_filter
from apps.filters.models import Filter


def create_int_filter(operation):
    return Filter(
        column="id",
        type=Filter.Type.INTEGER,
        numeric_predicate=operation,
        integer_value=42,
    )


def create_float_filter(operation):
    return Filter(
        column="stars",
        type=Filter.Type.FLOAT,
        numeric_predicate=operation,
        float_value=42.0,
    )


def create_string_filter(operation):
    return Filter(
        column="athlete",
        type=Filter.Type.STRING,
        string_predicate=operation,
        string_value="Adam Ondra",
    )


def create_bool_filter(value):
    return Filter(
        column="is_nice",
        type=Filter.Type.BOOL,
        bool_predicate=value,
    )


def create_time_filter(operation):
    return Filter(
        column="lunch",
        type=Filter.Type.TIME,
        time_predicate=operation,
        time_value="11:11:11.1111",
    )


def create_date_filter(operation):
    return Filter(
        column="birthday",
        type=Filter.Type.DATE,
        datetime_predicate=operation,
        date_value="1993-07-26",
    )


def create_datetime_filter(operation):
    return Filter(
        column="when",
        type=Filter.Type.DATETIME,
        datetime_predicate=operation,
        datetime_value="1993-07-26T06:30:12.1234",
    )


PARAMS = [
    pytest.param(
        create_int_filter(Filter.NumericPredicate.EQUAL),
        lambda d: d.id == 42,
        id="Integer equal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.NEQUAL,
        ),
        lambda d: (d.id != 42) | (d.id.isnull()),
        id="Integer not equal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.GREATERTHAN,
        ),
        lambda d: d.id > 42,
        id="Integer greaterthan",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.GREATERTHANEQUAL,
        ),
        lambda d: d.id >= 42,
        id="Integer greaterthanequal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.LESSTHAN,
        ),
        lambda d: d.id < 42,
        id="Integer lessthan",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.LESSTHANEQUAL,
        ),
        lambda d: d.id <= 42,
        id="Integer lessthanequal",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.ISNULL,
        ),
        lambda d: d.id.isnull(),
        id="Integer is null",
    ),
    pytest.param(
        create_int_filter(
            Filter.NumericPredicate.NOTNULL,
        ),
        lambda d: d.id.notnull(),
        id="Integer not null",
    ),
    pytest.param(
        Filter(
            column="id",
            type=Filter.Type.INTEGER,
            numeric_predicate=Filter.NumericPredicate.ISIN,
            integer_values=[42, 43],
        ),
        lambda d: d.id.isin([42, 43]),
        id="Integer is in",
    ),
    pytest.param(
        Filter(
            column="id",
            type=Filter.Type.INTEGER,
            numeric_predicate=Filter.NumericPredicate.NOTIN,
            integer_values=[42, 43],
        ),
        lambda d: (d.id.notin([42, 43])) | (d.id.isnull()),
        id="Integer not in",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.EQUAL),
        lambda d: d.stars == 42.0,
        id="Float equal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.NEQUAL),
        lambda d: (d.stars != 42.0) | (d.stars.isnull()),
        id="Float not equal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.GREATERTHAN),
        lambda d: d.stars > 42.0,
        id="Float greaterthan",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.GREATERTHANEQUAL),
        lambda d: d.stars >= 42.0,
        id="Float greaterthanequal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.LESSTHAN),
        lambda d: d.stars < 42.0,
        id="Float lessthan",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.LESSTHANEQUAL),
        lambda d: d.stars <= 42.0,
        id="Float lessthanequal",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.ISNULL),
        lambda d: d.stars.isnull(),
        id="Float is null",
    ),
    pytest.param(
        create_float_filter(Filter.NumericPredicate.NOTNULL),
        lambda d: d.stars.notnull(),
        id="Float not null",
    ),
    pytest.param(
        Filter(
            column="stars",
            type=Filter.Type.FLOAT,
            numeric_predicate=Filter.NumericPredicate.ISIN,
            float_values=[42.0, 42.3],
        ),
        lambda d: d.stars.isin([42.0, 42.3]),
        id="Float is in",
    ),
    pytest.param(
        Filter(
            column="stars",
            type=Filter.Type.FLOAT,
            numeric_predicate=Filter.NumericPredicate.NOTIN,
            float_values=[42.0, 42.3],
        ),
        lambda d: (d.stars.notin([42.0, 42.3])) | (d.stars.isnull()),
        id="Float not in",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.EQUAL),
        lambda d: d.athlete == "Adam Ondra",
        id="String equal",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NEQUAL),
        lambda d: (d.athlete != "Adam Ondra") | (d.athlete.isnull()),
        id="String not equal",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.CONTAINS),
        lambda d: d.athlete.contains("Adam Ondra"),
        id="String contains",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NOTCONTAINS),
        lambda d: ~d.athlete.contains("Adam Ondra"),
        id="String not contains",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.STARTSWITH),
        lambda d: d.athlete.startswith("Adam Ondra"),
        id="String starts with",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ENDSWITH),
        lambda d: d.athlete.endswith("Adam Ondra"),
        id="String ends with",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISNULL),
        lambda d: d.athlete.isnull(),
        id="String is null",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.NOTNULL),
        lambda d: d.athlete.notnull(),
        id="String not null",
    ),
    pytest.param(
        Filter(
            column="athlete",
            type=Filter.Type.STRING,
            string_predicate=Filter.StringPredicate.ISIN,
            string_values=["Janja Garnbret"],
        ),
        lambda d: d.athlete.isin(["Janja Garnbret"]),
        id="String is in",
    ),
    pytest.param(
        Filter(
            column="athlete",
            type=Filter.Type.STRING,
            string_predicate=Filter.StringPredicate.NOTIN,
            string_values=["Janja Garnbret"],
        ),
        lambda d: (d.athlete.notin(["Janja Garnbret"])) | (d.athlete.isnull()),
        id="String not in",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISUPPERCASE),
        lambda d: d.athlete == d.athlete.upper(),
        id="String is uppercase",
    ),
    pytest.param(
        create_string_filter(Filter.StringPredicate.ISLOWERCASE),
        lambda d: d.athlete == d.athlete.lower(),
        id="String is lowercase",
    ),
    pytest.param(
        create_bool_filter(Filter.BoolPredicate.ISTRUE),
        lambda d: d.is_nice,
        id="Bool is true",
    ),
    pytest.param(
        create_bool_filter(Filter.BoolPredicate.ISFALSE),
        lambda d: d.is_nice == False,
        id="Bool is false",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.ON),
        lambda d: d.lunch == "11:11:11.1111",
        id="Time on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.NOTON),
        lambda d: (d.lunch != "11:11:11.1111") | (d.lunch.isnull()),
        id="Time not on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.BEFORE),
        lambda d: d.lunch < "11:11:11.1111",
        id="Time before",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.BEFOREON),
        lambda d: d.lunch <= "11:11:11.1111",
        id="Time before on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.AFTER),
        lambda d: d.lunch > "11:11:11.1111",
        id="Time after",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.AFTERON),
        lambda d: d.lunch >= "11:11:11.1111",
        id="Time after on",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.ISNULL),
        lambda d: d.lunch.isnull(),
        id="Time is null",
    ),
    pytest.param(
        create_time_filter(Filter.TimePredicate.NOTNULL),
        lambda d: d.lunch.notnull(),
        id="Time not null",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.ON),
        lambda d: d.birthday == "1993-07-26",
        id="Date on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.NOTON),
        lambda d: (d.birthday != "1993-07-26") | (d.birthday.isnull()),
        id="Date not on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.BEFORE),
        lambda d: d.birthday < "1993-07-26",
        id="Date before",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.BEFOREON),
        lambda d: d.birthday <= "1993-07-26",
        id="Date before on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.AFTER),
        lambda d: d.birthday > "1993-07-26",
        id="Date after",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.AFTERON),
        lambda d: d.birthday >= "1993-07-26",
        id="Date after on",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.ISNULL),
        lambda d: d.birthday.isnull(),
        id="Date is null",
    ),
    pytest.param(
        create_date_filter(Filter.TimePredicate.NOTNULL),
        lambda d: d.birthday.notnull(),
        id="Date not null",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.ON),
        lambda d: d.when == "1993-07-26T06:30:12.1234",
        id="Datetime on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.NOTON),
        lambda d: (d.when != "1993-07-26T06:30:12.1234") | (d.when.isnull()),
        id="Datetime not on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.BEFORE),
        lambda d: d.when < "1993-07-26T06:30:12.1234",
        id="Datetime before",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.BEFOREON),
        lambda d: d.when <= "1993-07-26T06:30:12.1234",
        id="Datetime before on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.AFTER),
        lambda d: d.when > "1993-07-26T06:30:12.1234",
        id="Datetime after",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.AFTERON),
        lambda d: d.when >= "1993-07-26T06:30:12.1234",
        id="Datetime after on",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.ISNULL),
        lambda d: d.when.isnull(),
        id="Datetime is null",
    ),
    pytest.param(
        create_datetime_filter(Filter.TimePredicate.NOTNULL),
        lambda d: d.when.notnull(),
        id="Datetime not null",
    ),
]


@pytest.mark.parametrize("filter_, get_condition", PARAMS)
def test_filters(engine, filter_, get_condition):
    query = get_query_from_filter(engine.data, filter_)
    assert query.equals(engine.data[get_condition(engine.data)])


def get_predicate(param):
    f = param.values[0]

    return (
        f.numeric_predicate
        or f.time_predicate
        or f.datetime_predicate
        or f.string_predicate
    )


def test_all_filters_tested():
    tested = set(map(get_predicate, PARAMS))
    # Boolean test has no  predicate
    assert tested == {
        None,
        *Filter.NumericPredicate,
        *Filter.StringPredicate,
        *Filter.TimePredicate,
    }
