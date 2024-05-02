import ibis
import pytest

from apps.columns.engine import (
    PART_MAP,
    DatePeriod,
    aggregate_columns,
    compile_function,
    get_groups,
)
from apps.columns.models import EditColumn

pytestmark = pytest.mark.django_db

TYPE_COLUMN_MAP = {
    "Integer": "id",
    "String": "athlete",
    "Time": "lunch",
    "Date": "birthday",
    "Datetime": "when",
}


def no_arg_func_param(function, type_):
    return pytest.param(
        function,
        type_,
        id=f"{type_} {function}",
    )


@pytest.mark.parametrize(
    "function, type_",
    [
        no_arg_func_param("isnull", "Integer"),
        no_arg_func_param("notnull", "Integer"),
        no_arg_func_param("abs", "Integer"),
        no_arg_func_param("isnull", "String"),
        no_arg_func_param("notnull", "String"),
        no_arg_func_param("lower", "String"),
        no_arg_func_param("upper", "String"),
        no_arg_func_param("length", "String"),
        no_arg_func_param("reverse", "String"),
        no_arg_func_param("strip", "String"),
        no_arg_func_param("lstrip", "String"),
        no_arg_func_param("rstrip", "String"),
        no_arg_func_param("isnull", "Time"),
        no_arg_func_param("notnull", "Time"),
        no_arg_func_param("isnull", "Date"),
        no_arg_func_param("notnull", "Date"),
        no_arg_func_param("isnull", "Datetime"),
        no_arg_func_param("notnull", "Datetime"),
        no_arg_func_param("cummax", "Integer"),
        no_arg_func_param("cummin", "Integer"),
        no_arg_func_param("sqrt", "Integer"),
        no_arg_func_param("ceil", "Integer"),
        no_arg_func_param("floor", "Integer"),
        no_arg_func_param("ln", "Integer"),
        no_arg_func_param("log2", "Integer"),
        no_arg_func_param("log10", "Integer"),
        no_arg_func_param("exp", "Integer"),
        no_arg_func_param("time", "Datetime"),
        no_arg_func_param("date", "Datetime"),
        no_arg_func_param("epoch_seconds", "Datetime"),
        no_arg_func_param("hour", "Time"),
        no_arg_func_param("minute", "Time"),
        no_arg_func_param("second", "Time"),
        no_arg_func_param("millisecond", "Time"),
        no_arg_func_param("year", "Date"),
        no_arg_func_param("month", "Date"),
        no_arg_func_param("day", "Date"),
        no_arg_func_param("year", "Datetime"),
        no_arg_func_param("month", "Datetime"),
        no_arg_func_param("day", "Datetime"),
        no_arg_func_param("hour", "Datetime"),
        no_arg_func_param("minute", "Datetime"),
        no_arg_func_param("second", "Datetime"),
        no_arg_func_param("millisecond", "Datetime"),
    ],
)
def test_no_arg_function(engine, function, type_):
    column = TYPE_COLUMN_MAP[type_]
    edit = EditColumn(column=column, **{f"{type_.lower()}_function": function})
    query = compile_function(engine.data, edit)
    assert query.equals(getattr(engine.data[column], function)())


def unary_func_param(function, type_, arg):
    return pytest.param(function, type_, arg, id=f"{type_} {function}")


@pytest.mark.parametrize(
    "function, type_, arg",
    [
        unary_func_param("log", "Integer", 42.0),
        unary_func_param("add", "Integer", 42.0),
        unary_func_param("sub", "Integer", 42.0),
        unary_func_param("mul", "Integer", 42.0),
        unary_func_param("div", "Integer", 42.0),
        unary_func_param("fillna", "String", "Sascha Hofmann"),
        unary_func_param("like", "String", "David %"),
    ],
)
def test_unary_function(engine, function, type_, arg):
    column = TYPE_COLUMN_MAP[type_]
    edit = EditColumn(
        column=column,
        **{
            f"{type_.lower()}_function": function,
            f"{'string' if type_=='String' else 'float'}_value": arg,
        },
    )
    query = compile_function(engine.data, edit)
    assert query.equals(getattr(engine.data[column], function)(arg))


PARAMS = [
    pytest.param(
        "birthday",
        DatePeriod.MONTH,
        id="month",
    ),
    pytest.param(
        "birthday",
        DatePeriod.WEEK,
        id="week",
    ),
    pytest.param(
        "birthday",
        DatePeriod.MONTH_ONLY,
        id="month only",
    ),
    pytest.param(
        "when",
        DatePeriod.DATE,
        id="date",
    ),
    pytest.param(
        "birthday",
        DatePeriod.YEAR,
        id="year",
    ),
    pytest.param(
        "birthday",
        DatePeriod.QUARTER,
        id="quarter",
    ),
]


@pytest.mark.parametrize("name, part", PARAMS)
def test_column_part_group(name, part, column_factory, node_factory, engine):
    node = node_factory()
    column_factory(column=name, part=part, node=node)
    groups = get_groups(engine.data, node)
    query = aggregate_columns(engine.data, node.aggregations.all(), groups)
    assert query.equals(
        engine.data.group_by(**{name: PART_MAP[part](engine.data[name])}).aggregate(
            count=ibis._.count()
        )
    )


def test_all_parts_tested():
    tested_parts = {test.values[1] for test in PARAMS}
    assert tested_parts == set(DatePeriod)
