import ibis
import ibis_bigquery
import pytest
from apps.columns.bigquery import compile_formula

TABLE = ibis.table(
    [
        ("id", "int32"),
        ("athlete", "string"),
        ("birthday", "date"),
        ("updated", "timestamp"),
        ("medals", "int32"),
        ("stars", "double"),
    ],
    name="olympians",
)

BASE_QUERY = "SELECT {} AS `tmp`\nFROM olympians"


def create_str_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(athlete)",
        BASE_QUERY.format(f"{sql_name or func_name}(`athlete`)"),
        id=func_name,
    )


def create_int_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(medals)",
        BASE_QUERY.format(f"{sql_name or func_name}(`medals`)"),
        id=func_name,
    )


def create_datetime_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(updated)",
        BASE_QUERY.format(f"{sql_name or func_name}(`updated`)"),
        id=func_name,
    )


def create_extract_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(updated)",
        BASE_QUERY.format(f"EXTRACT({sql_name or func_name} from `updated`)"),
        id=func_name,
    )


@pytest.mark.parametrize(
    "formula, expected_sql",
    [
        pytest.param(
            "isnull(athlete)",
            BASE_QUERY.format("`athlete` IS NULL"),
            id="is null",
        ),
        pytest.param(
            "notnull(stars)",
            BASE_QUERY.format("`stars` IS NOT NULL"),
            id="not null",
        ),
        pytest.param(
            'fillna(athlete, "Usain Bolt")',
            BASE_QUERY.format("IFNULL(`athlete`, 'Usain Bolt')"),
            id="fill NA",
        ),
        # Test string operations
        create_str_unary_param("lower"),
        create_str_unary_param("hash"),
        pytest.param(
            'join(", ", athlete, "that genius")',
            BASE_QUERY.format("ARRAY_TO_STRING([`athlete`, 'that genius'], ', ')"),
            id="join",
        ),
        create_str_unary_param("upper"),
        create_str_unary_param("length"),
        create_str_unary_param("reverse"),
        create_str_unary_param("strip", "trim"),
        create_str_unary_param("lstrip", "ltrim"),
        create_str_unary_param("rstrip", "rtrim"),
        pytest.param(
            'like(athlete, "Tom Daley")',
            BASE_QUERY.format("`athlete` LIKE 'Tom Daley'"),
            id="like",
        ),
        pytest.param(
            'contains(athlete, "Usain Bolt")',
            BASE_QUERY.format("IFNULL(`athlete`, 'Usain Bolt')"),
            id="contains",
        ),
        pytest.param(
            "left(athlete, 2)",
            BASE_QUERY.format("IFNULL(`athlete`, 'Usain Bolt')"),
            id="left",
        ),
        pytest.param(
            "right(athlete, 4)",
            BASE_QUERY.format("IFNULL(`athlete`, 'Usain Bolt')"),
            id="right",
        ),
        pytest.param(
            "repeat(athlete, 2)",
            BASE_QUERY.format("REPEAT(`athlete`, 2)"),
            id="repeat",
        ),
        # Test numeric operations
        create_int_unary_param("abs"),
        pytest.param(
            "add(medals, stars)",
            BASE_QUERY.format("`medals` + `stars`"),
            id="add integer and float columns",
        ),
        pytest.param(
            "medals + 5",
            BASE_QUERY.format("`medals` + 5"),
            id="add integer scalar to integer column",
        ),
        create_int_unary_param("ceil"),
        pytest.param(
            "divide(medals, stars)",
            BASE_QUERY.format("IEEE_DIVIDE(`medals`, `stars`)"),
            id="div integer and float columns",
        ),
        pytest.param(
            "medals / 42",
            BASE_QUERY.format("IEEE_DIVIDE(`medals`, 42)"),
            id="div integer column and integer scalar",
        ),
        create_int_unary_param("exp"),
        pytest.param(
            "floor(stars)",
            BASE_QUERY.format("CAST(FLOOR(`stars`) AS INT64)"),
            id="floor",
        ),
        create_int_unary_param("sqrt"),
        create_int_unary_param("ln"),
        pytest.param(
            "log(medals, 3)",
            BASE_QUERY.format("log(`medals`, 3)"),
            id="log",
        ),
        pytest.param(
            "log2(medals)",
            BASE_QUERY.format("log(`medals`, 2)"),
            id="log2",
        ),
        create_int_unary_param("log10"),
        pytest.param(
            "mul(stars, medals)",
            BASE_QUERY.format("`stars` * `medals`"),
            id="multiply int and float column",
        ),
        pytest.param(
            "stars * 42",
            BASE_QUERY.format("`stars` * 42"),
            id="multiply float column and int scalar",
        ),
        pytest.param(
            "pow(stars, medals)",
            BASE_QUERY.format("pow(`stars`, `medals`)"),
            id="float column to the power of int column",
        ),
        # Test datetime operations
        create_extract_unary_param("year"),
        create_datetime_unary_param("time", "TIME"),
        create_datetime_unary_param("date", "DATE"),
        create_extract_unary_param("second"),
        create_extract_unary_param("month"),
        create_extract_unary_param("minute"),
        create_extract_unary_param("millisecond"),
        create_extract_unary_param("hour"),
        create_datetime_unary_param("epoch_seconds", "UNIX_SECONDS"),
        create_datetime_unary_param("day_of_week"),
        create_extract_unary_param("day"),
    ],
)
def test_formula(formula, expected_sql):
    sql = ibis_bigquery.compile(compile_formula(TABLE, formula))
    assert sql == expected_sql
