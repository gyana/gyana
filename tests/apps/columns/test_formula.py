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


def create_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(athlete)",
        BASE_QUERY.format(f"{sql_name or func_name}(`athlete`)"),
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
        create_unary_param("lower"),
        create_unary_param("upper"),
        create_unary_param("length"),
        create_unary_param("reverse"),
        create_unary_param("strip"),
        create_unary_param("lstrip"),
        create_unary_param("rstrip"),
        pytest.param(
            'like(athlete, "Tom Daley")',
            BASE_QUERY.format("`athlete` LIKE Tom Daley"),
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
    ],
)
def test_formula(formula, expected_sql):
    sql = ibis_bigquery.compile(compile_formula(TABLE, formula))
    assert sql == expected_sql
