import ibis_bigquery
import pytest
from apps.base.tests.mock_data import TABLE
from apps.columns.bigquery import compile_function
from apps.columns.forms import OperationColumnForm
from apps.columns.models import EditColumn

QUERY = """SELECT {} AS `tmp`
FROM olympians"""


def create_extract_edit(column, extraction, type_):
    return pytest.param(
        EditColumn(column=column, **{f"{type_.lower()}_function": extraction}),
        QUERY.format(f"EXTRACT({extraction} from `{column}`)"),
        id=f"{type_} {extraction}",
    )


@pytest.mark.parametrize(
    "edit, expected_sql",
    [
        # Numeric edit
        pytest.param(
            EditColumn(column="id", integer_function="isnull"),
            QUERY.format("`id` IS NULL"),
            id="Integer isnull",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="notnull"),
            QUERY.format("`id` IS NOT NULL"),
            id="Integer notnull",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="cummax"),
            QUERY.format(
                "max(`id`) OVER (RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"
            ),
            id="Integer cummax",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="cummin"),
            QUERY.format(
                "min(`id`) OVER (RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"
            ),
            id="Integer cummin",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="abs"),
            QUERY.format("abs(`id`)"),
            id="Integer abs",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="sqrt"),
            QUERY.format("sqrt(`id`)"),
            id="Integer sqrt",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="ceil"),
            QUERY.format("ceil(`id`)"),
            id="Integer ceil",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="floor"),
            QUERY.format("CAST(FLOOR(`id`) AS INT64)"),
            id="Integer floor",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="ln"),
            QUERY.format("ln(`id`)"),
            id="Integer ln",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="log2"),
            QUERY.format("log(`id`, 2)"),
            id="Integer log2",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="log10"),
            QUERY.format("log10(`id`)"),
            id="Integer log10",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="log", float_value=42.0),
            QUERY.format("log(`id`, 42.0)"),
            id="Integer log",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="exp"),
            QUERY.format("exp(`id`)"),
            id="Integer exp",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="add", float_value=42.0),
            QUERY.format("`id` + 42.0"),
            id="Integer add",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="sub", float_value=42.0),
            QUERY.format("`id` - 42.0"),
            id="Integer subtract",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="mul", float_value=42.0),
            QUERY.format("`id` * 42.0"),
            id="Integer mul",
        ),
        pytest.param(
            EditColumn(column="id", integer_function="div", float_value=42.0),
            QUERY.format("IEEE_DIVIDE(`id`, 42.0)"),
            id="Integer div",
        ),
        # String edit
        pytest.param(
            EditColumn(column="athlete", string_function="isnull"),
            QUERY.format("`athlete` IS NULL"),
            id="String is null",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="notnull"),
            QUERY.format("`athlete` IS NOT NULL"),
            id="String not null",
        ),
        pytest.param(
            EditColumn(
                column="athlete",
                string_function="fillna",
                string_value="Sascha Hofmann",
            ),
            QUERY.format("IFNULL(`athlete`, 'Sascha Hofmann')"),
            id="String fillna",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="lower"),
            QUERY.format("lower(`athlete`)"),
            id="String lower",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="upper"),
            QUERY.format("upper(`athlete`)"),
            id="String upper",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="length"),
            QUERY.format("length(`athlete`)"),
            id="String length",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="reverse"),
            QUERY.format("reverse(`athlete`)"),
            id="String reverse",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="strip"),
            QUERY.format("trim(`athlete`)"),
            id="String strip",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="lstrip"),
            QUERY.format("ltrim(`athlete`)"),
            id="String lstrip",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="rstrip"),
            QUERY.format("rtrim(`athlete`)"),
            id="String rstrip",
        ),
        pytest.param(
            EditColumn(
                column="athlete", string_function="like", string_value="David %"
            ),
            QUERY.format("`athlete` LIKE 'David %'"),
            id="String like",
        ),
        # Time edit
        pytest.param(
            EditColumn(column="lunch", time_function="isnull"),
            QUERY.format("`lunch` IS NULL"),
            id="Time is null",
        ),
        pytest.param(
            EditColumn(column="lunch", time_function="notnull"),
            QUERY.format("`lunch` IS NOT NULL"),
            id="Time not null",
        ),
        create_extract_edit("lunch", "hour", "Time"),
        create_extract_edit("lunch", "minute", "Time"),
        create_extract_edit("lunch", "second", "Time"),
        create_extract_edit("lunch", "millisecond", "Time"),
        # Date edit
        pytest.param(
            EditColumn(column="birthday", date_function="isnull"),
            QUERY.format("`birthday` IS NULL"),
            id="Date is null",
        ),
        pytest.param(
            EditColumn(column="birthday", date_function="notnull"),
            QUERY.format("`birthday` IS NOT NULL"),
            id="Date not null",
        ),
        create_extract_edit("birthday", "year", "Date"),
        create_extract_edit("birthday", "month", "Date"),
        create_extract_edit("birthday", "day", "Date"),
        #  Datetime edit
        pytest.param(
            EditColumn(column="updated", date_function="isnull"),
            QUERY.format("`updated` IS NULL"),
            id="Datetime is null",
        ),
        pytest.param(
            EditColumn(column="updated", date_function="notnull"),
            QUERY.format("`updated` IS NOT NULL"),
            id="Datetime not null",
        ),
        create_extract_edit("updated", "year", "Datetime"),
        create_extract_edit("updated", "month", "Datetime"),
        create_extract_edit("updated", "day", "Datetime"),
        create_extract_edit("updated", "hour", "Datetime"),
        create_extract_edit("updated", "minute", "Datetime"),
        create_extract_edit("updated", "second", "Datetime"),
        create_extract_edit("updated", "millisecond", "Datetime"),
        pytest.param(
            EditColumn(column="updated", datetime_function="time"),
            QUERY.format("TIME(`updated`)"),
            id="Datetime time",
        ),
        pytest.param(
            EditColumn(column="updated", datetime_function="date"),
            QUERY.format("DATE(`updated`)"),
            id="Datetime date",
        ),
        pytest.param(
            EditColumn(column="updated", datetime_function="epoch_seconds"),
            QUERY.format("UNIX_SECONDS(`updated`)"),
            id="Datetime epoch seconds",
        ),
    ],
)
def test_compile_function(edit, expected_sql):
    sql = ibis_bigquery.compile(compile_function(TABLE, edit))
    assert sql == expected_sql


@pytest.mark.parametrize(
    "edit, fields",
    [
        pytest.param(EditColumn(), ["column"], id="Empty edit"),
        pytest.param(
            EditColumn(column="id"), ["column", "integer_function"], id="Integer column"
        ),
        pytest.param(
            EditColumn(column="id", integer_function="sub"),
            ["column", "integer_function", "float_value"],
            id="Integer column with function",
        ),
        pytest.param(
            EditColumn(column="stars", integer_function="sub"),
            ["column", "integer_function", "float_value"],
            id="Float column",
        ),
        pytest.param(
            EditColumn(column="athlete"),
            ["column", "string_function"],
            id="String column",
        ),
        pytest.param(
            EditColumn(column="athlete", string_function="like"),
            ["column", "string_function", "string_value"],
            id="String column with function",
        ),
        pytest.param(
            EditColumn(column="updated"),
            ["column", "datetime_function"],
            id="Datetime column",
        ),
        pytest.param(
            EditColumn(column="birthday"), ["column", "date_function"], id="Date column"
        ),
        pytest.param(
            EditColumn(column="lunch"), ["column", "time_function"], id="Time column"
        ),
    ],
)
def test_edit_live_fields(edit, fields):
    form = OperationColumnForm(schema=TABLE.schema(), instance=edit)
    assert form.get_live_fields() == fields
