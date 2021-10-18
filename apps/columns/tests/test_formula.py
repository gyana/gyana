import ibis_bigquery
import pytest
from apps.base.tests.mock_data import TABLE
from apps.columns.bigquery import compile_formula

QUERY = "SELECT {} AS `tmp`\nFROM olympians"


def create_str_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(athlete)",
        QUERY.format(f"{sql_name or func_name}(`athlete`)"),
        id=func_name,
    )


def create_int_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(medals)",
        QUERY.format(f"{sql_name or func_name}(`medals`)"),
        id=func_name,
    )


def create_datetime_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(updated)",
        QUERY.format(f"{sql_name or func_name}(`updated`)"),
        id=func_name,
    )


def create_extract_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(updated)",
        QUERY.format(f"EXTRACT({sql_name or func_name} from `updated`)"),
        id=func_name,
    )


@pytest.mark.parametrize(
    "formula, expected_sql",
    [
        pytest.param(
            "isnull(athlete)",
            QUERY.format("`athlete` IS NULL"),
            id="is null",
        ),
        pytest.param(
            "notnull(stars)",
            QUERY.format("`stars` IS NOT NULL"),
            id="not null",
        ),
        pytest.param(
            'fillna(athlete, "Usain Bolt")',
            QUERY.format("IFNULL(`athlete`, 'Usain Bolt')"),
            id="fill NA",
        ),
        pytest.param(
            'cast(medals, "float")',
            QUERY.format("CAST(`medals` AS FLOAT64)"),
            id="cast int to float",
        ),
        pytest.param(
            'cast(athlete, "timestamp")',
            QUERY.format("CAST(`athlete` AS TIMESTAMP)"),
            id="cast string to datetime",
        ),
        pytest.param(
            'cast(birthday, "str")',
            QUERY.format("CAST(`birthday` AS STRING)"),
            id="cast date to string",
        ),
        pytest.param(
            "coalesce(id, medals, stars)",
            QUERY.format("coalesce(`id`, `medals`, `stars`)"),
            id="coalesce",
        ),
        pytest.param(
            "ifelse(is_nice, medals*10, medals-5)",
            QUERY.format(
                "CASE WHEN `is_nice` THEN `medals` * 10 ELSE `medals` - 5 END"
            ),
            id="if else",
        ),
        # Test string operations
        pytest.param(
            'between(athlete, "Rafael Nadal" , "Roger Federer")',
            QUERY.format("`athlete` BETWEEN 'Rafael Nadal' AND 'Roger Federer'"),
            id="between string column",
        ),
        pytest.param(
            'find(athlete, "Kipchoge")',
            QUERY.format("STRPOS(`athlete`, 'Kipchoge') - 1"),
            id="find no optional arguments",
        ),
        create_str_unary_param("lower"),
        pytest.param(
            "lpad(athlete,3)",
            QUERY.format("lpad(`athlete`, 3, ' ')"),
            id="lpad no optional argument",
        ),
        pytest.param(
            'lpad(athlete,3, "\n")',
            # for some reason ibis adds a random newlineafter the select
            "SELECT\n  lpad(`athlete`, 3, '\n  ') AS `tmp`\nFROM olympians",
            id="lpad with fillchar",
        ),
        pytest.param(
            "hash(athlete)",
            QUERY.format("farm_fingerprint(`athlete`)"),
            id="hash",
        ),
        pytest.param(
            'join(", ", athlete, "that genius")',
            QUERY.format("ARRAY_TO_STRING([`athlete`, 'that genius'], ', ')"),
            id="join",
        ),
        create_str_unary_param("upper"),
        create_str_unary_param("length"),
        create_str_unary_param("reverse"),
        create_str_unary_param("strip", "trim"),
        create_str_unary_param("lstrip", "ltrim"),
        create_str_unary_param("rstrip", "rtrim"),
        pytest.param(
            "rpad(athlete,3)",
            QUERY.format("rpad(`athlete`, 3, ' ')"),
            id="rpad no optional argument",
        ),
        pytest.param(
            'rpad(athlete,3, "\n")',
            # for some reason ibis adds a random newlineafter the select
            "SELECT\n  rpad(`athlete`, 3, '\n  ') AS `tmp`\nFROM olympians",
            id="rpad with fillchar",
        ),
        pytest.param(
            'like(athlete, "Tom Daley")',
            QUERY.format("`athlete` LIKE 'Tom Daley'"),
            id="like",
        ),
        pytest.param(
            'contains(athlete, "Usain Bolt")',
            QUERY.format("STRPOS(`athlete`, 'Usain Bolt') - 1 >= 0"),
            id="contains",
        ),
        pytest.param(
            "repeat(athlete, 2)",
            QUERY.format("REPEAT(`athlete`, 2)"),
            id="repeat",
        ),
        pytest.param(
            're_extract(athlete, "ough", 2)',
            QUERY.format("REGEXP_EXTRACT_ALL(`athlete`, r'ough')[SAFE_OFFSET(2)]"),
            id="re_extract",
        ),
        pytest.param(
            're_replace(athlete, "ough", "uff")',
            QUERY.format("REGEXP_REPLACE(`athlete`, r'ough', 'uff')"),
            id="re_replace",
        ),
        pytest.param(
            're_search(athlete, "Will.*")',
            QUERY.format("REGEXP_CONTAINS(`athlete`, r'Will.*')"),
            id="re_search",
        ),
        pytest.param(
            'replace(athlete, "ough", "uff")',
            QUERY.format("REPLACE(`athlete`, 'ough', 'uff')"),
            id="replace",
        ),
        pytest.param(
            'substitute(athlete, "Tim")',
            QUERY.format("CASE `athlete` WHEN 'Tim' THEN NULL ELSE `athlete` END"),
            id="substitute no optional arguments",
        ),
        pytest.param(
            'substitute(athlete, "Tim", "Tom")',
            QUERY.format("CASE `athlete` WHEN 'Tim' THEN 'Tom' ELSE `athlete` END"),
            id="substitute with replace argument",
        ),
        pytest.param(
            'substitute(athlete, "Tim", "Tom", "Till")',
            QUERY.format("CASE `athlete` WHEN 'Tim' THEN 'Tom' ELSE 'Till' END"),
            id="substitute with both arguments",
        ),
        # Test numeric operations
        create_int_unary_param("abs"),
        pytest.param(
            "add(medals, stars)",
            QUERY.format("`medals` + `stars`"),
            id="add integer and float columns",
        ),
        pytest.param(
            "medals + 5",
            QUERY.format("`medals` + 5"),
            id="add integer scalar to integer column",
        ),
        pytest.param(
            "between(medals,2,10)",
            QUERY.format("`medals` BETWEEN 2 AND 10"),
            id="between integer column",
        ),
        create_int_unary_param("ceil"),
        pytest.param(
            "divide(medals, stars)",
            QUERY.format("IEEE_DIVIDE(`medals`, `stars`)"),
            id="div integer and float columns",
        ),
        pytest.param(
            "medals / 42",
            QUERY.format("IEEE_DIVIDE(`medals`, 42)"),
            id="div integer column and integer scalar",
        ),
        create_int_unary_param("exp"),
        pytest.param(
            "floor(stars)",
            QUERY.format("CAST(FLOOR(`stars`) AS INT64)"),
            id="floor",
        ),
        create_int_unary_param("sqrt"),
        create_int_unary_param("ln"),
        pytest.param(
            "log(medals, 3)",
            QUERY.format("log(`medals`, 3)"),
            id="log",
        ),
        pytest.param(
            "log2(medals)",
            QUERY.format("log(`medals`, 2)"),
            id="log2",
        ),
        create_int_unary_param("log10"),
        pytest.param(
            "mul(stars, medals)",
            QUERY.format("`stars` * `medals`"),
            id="multiply int and float column",
        ),
        pytest.param(
            "round(stars, 2)",
            QUERY.format("round(`stars`, 2)"),
            id="round",
        ),
        pytest.param(
            "stars * 42",
            QUERY.format("`stars` * 42"),
            id="multiply float column and int scalar",
        ),
        pytest.param(
            "pow(stars, medals)",
            QUERY.format("pow(`stars`, `medals`)"),
            id="float column to the power of int column",
        ),
        pytest.param(
            "sub(stars, medals)",
            QUERY.format("`stars` - `medals`"),
            id="subtract int column from float column",
        ),
        pytest.param(
            "stars - 42.0",
            QUERY.format("`stars` - 42.0"),
            id="subtract float scalar from float column",
        ),
        pytest.param(
            'datetime_seconds(medals, "s")',
            QUERY.format("TIMESTAMP_SECONDS(`medals`)"),
            id="integer column to datetime",
        ),
        pytest.param(
            'datetime_seconds(131313131313, "ms")',
            "SELECT TIMESTAMP_MILLIS(131313131313) AS `tmp`",
            id="integer to datetime",
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
        create_extract_unary_param("day"),
        pytest.param(
            "between(birthday, 1990-01-01, 2000-07-01)",
            QUERY.format("`birthday` BETWEEN '1990-01-01' AND '2000-07-01'"),
            id="between date column",
        ),
        pytest.param(
            'strftime(updated,"%d-%m")',
            QUERY.format("FORMAT_TIMESTAMP('%d-%m', `updated`, 'UTC')"),
            id="strftime",
        ),
        pytest.param(
            'truncate(updated, "ms")',
            QUERY.format("TIMESTAMP_TRUNC(`updated`, MILLISECOND)"),
            id="truncate milliseconds from datetime",
        ),
        pytest.param(
            'truncate(birthday, "d")',
            QUERY.format("DATE_TRUNC(`birthday`, DAY)"),
            id="truncate day from date",
        ),
        pytest.param(
            "updated - updated",
            QUERY.format("TIMESTAMP_DIFF(`updated`, `updated`, SECOND)"),
            id="datetime difference",
        ),
        pytest.param(
            "birthday - birthday",
            QUERY.format("DATE_DIFF(`birthday`, `birthday`, DAY)"),
            id="date difference",
        ),
        pytest.param(
            "lunch - lunch",
            QUERY.format("TIME_DIFF(`lunch`, `lunch`, SECOND)"),
            id="time difference",
        ),
        pytest.param(
            'datetime_diff(updated, updated, "Y")',
            QUERY.format("TIMESTAMP_DIFF(`updated`, `updated`, YEAR)"),
            id="datetime datetime_diff",
        ),
        pytest.param(
            'datetime_diff(time(updated), lunch, "m")',
            QUERY.format("TIME_DIFF(TIME(`updated`), `lunch`, MINUTE)"),
            id="time datetime_diff",
        ),
        pytest.param(
            'datetime_diff(date(updated), updated, "W")',
            QUERY.format("DATE_DIFF(DATE(`updated`), `updated`, WEEK)"),
            id="date datetime_diff",
        ),
        # Test nested functions
        pytest.param(
            "(medals + stars)/(stars - 42) * medals",
            QUERY.format("(IEEE_DIVIDE(`medals` + `stars`, `stars` - 42)) * `medals`"),
            id="arithmetic formula mixing different operation",
        ),
        pytest.param(
            'upper(replace(athlete, "ff", "f"))',
            QUERY.format("upper(REPLACE(`athlete`, 'ff', 'f'))"),
            id="nest two string methods",
        ),
        pytest.param(
            "round(exp(month(birthday)*medals))",
            QUERY.format("round(exp(EXTRACT(month from `birthday`) * `medals`))"),
            id="nest numeric and datetime operations",
        ),
        pytest.param(
            'ifelse(between(birthday, 2000-01-01, 2000-01-31), "millenium kid", "normal kid")',
            QUERY.format(
                "CASE WHEN `birthday` BETWEEN '2000-01-01' AND '2000-01-31' THEN 'millenium kid' ELSE 'normal kid' END"
            ),
            id="nest ifelse with datetime function",
        ),
    ],
)
def test_formula(formula, expected_sql):
    sql = ibis_bigquery.compile(compile_formula(TABLE, formula))
    assert sql == expected_sql
