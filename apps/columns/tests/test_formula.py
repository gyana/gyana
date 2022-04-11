import ibis_bigquery
import pytest

from apps.base.tests.mock_data import TABLE
from apps.columns.bigquery import compile_formula
from apps.columns.transformer import FUNCTIONS

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
        f"{func_name}(when)",
        QUERY.format(f"{sql_name or func_name}(`when`)"),
        id=func_name,
    )


def create_extract_unary_param(func_name, sql_name=None):
    return pytest.param(
        f"{func_name}(when)",
        QUERY.format(f"EXTRACT({sql_name or func_name} from `when`)"),
        id=func_name,
    )


PARAMS = [
    pytest.param(
        "isnull(athlete)",
        QUERY.format("`athlete` IS NULL"),
        id="isnull",
    ),
    pytest.param(
        "notnull(stars)",
        QUERY.format("`stars` IS NOT NULL"),
        id="notnull",
    ),
    pytest.param(
        'fillnull(athlete, "Usain Bolt")',
        QUERY.format("IFNULL(`athlete`, 'Usain Bolt')"),
        id="fillnull",
    ),
    pytest.param(
        'convert(medals, "float")',
        QUERY.format("CAST(`medals` AS FLOAT64)"),
        id="convert int to float",
    ),
    pytest.param(
        'convert(athlete, "timestamp")',
        QUERY.format("CAST(`athlete` AS TIMESTAMP)"),
        id="convert string to datetime",
    ),
    pytest.param(
        'convert(birthday, "str")',
        QUERY.format("CAST(`birthday` AS STRING)"),
        id="convert date to string",
    ),
    pytest.param(
        "coalesce(id, medals, stars)",
        QUERY.format("coalesce(`id`, `medals`, `stars`)"),
        id="coalesce",
    ),
    pytest.param(
        "ifelse(is_nice, medals*10, medals-5)",
        QUERY.format("CASE WHEN `is_nice` THEN `medals` * 10 ELSE `medals` - 5 END"),
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
    pytest.param(
        'json_extract(\'{"class":{"id": 3}}\', "$.class.id")',
        "SELECT JSON_QUERY('{\"class\":{\"id\": 3}}', '$.class.id') AS `tmp`",
        id="json_extract",
    ),
    create_str_unary_param("upper"),
    create_str_unary_param("length"),
    create_str_unary_param("reverse"),
    create_str_unary_param("trim"),
    create_str_unary_param("ltrim"),
    create_str_unary_param("rtrim"),
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
        'regex_extract(athlete, "ough", 2)',
        QUERY.format("REGEXP_EXTRACT_ALL(`athlete`, r'ough')[SAFE_OFFSET(2)]"),
        id="regex_extract",
    ),
    pytest.param(
        'regex_replace(athlete, "ough", "uff")',
        QUERY.format("REGEXP_REPLACE(`athlete`, r'ough', 'uff')"),
        id="regex_replace",
    ),
    pytest.param(
        'regex_search(athlete, "Will.*")',
        QUERY.format("REGEXP_CONTAINS(`athlete`, r'Will.*')"),
        id="regex_search",
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
    pytest.param(
        "left(athlete, 4)", QUERY.format("substr(`athlete`, 0 + 1, 4)"), id="left"
    ),
    pytest.param(
        "right(athlete, 4)",
        QUERY.format("SUBSTR(`athlete`, -LEAST(LENGTH(`athlete`), 4))"),
        id="right",
    ),
    pytest.param(
        "parse_date(athlete, '%Y-%m-%d')",
        QUERY.format("PARSE_DATE('%Y-%m-%d', `athlete`)", id="parse_date"),
    ),
    pytest.param(
        "parse_time(athlete, '%H:%M:%S')",
        QUERY.format("PARSE_TIME('%H:%M:%S', `athlete`)", id="parse_time"),
    ),
    pytest.param(
        "parse_datetime(athlete, '%Y-%m-%dT%H:%M:%S')",
        QUERY.format(
            "PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S', `athlete`)", id="parse_datetime"
        ),
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
    create_int_unary_param("ceiling", "ceil"),
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
        "product(stars, medals)",
        QUERY.format("`stars` * `medals`"),
        id="multiply int and float column",
    ),
    pytest.param(
        "medals % 3",
        QUERY.format("MOD(`medals`, 3)"),
        id="modulo integer column and integer scalar",
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
        "power(stars, medals)",
        QUERY.format("pow(`stars`, `medals`)"),
        id="float column to the power of int column",
    ),
    pytest.param(
        "subtract(stars, medals)",
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
    pytest.param(
        "date(1993,07, medals)",
        QUERY.format(
            "PARSE_DATE('%Y-%m-%d', CONCAT(CONCAT(CONCAT(CONCAT(CAST(1993 AS STRING), '-'), CAST(7 AS STRING)), '-'), CAST(`medals` AS STRING)))"
        ),
        id="date",
    ),
    pytest.param(
        "time(12,12, medals)",
        QUERY.format(
            "PARSE_TIME('%H:%M:%S', CONCAT(CONCAT(CONCAT(CONCAT(CAST(12 AS STRING), ':'), CAST(12 AS STRING)), ':'), CAST(`medals` AS STRING)))"
        ),
        id="time",
    ),
    pytest.param("today()", "SELECT CURRENT_DATE() AS `tmp`", id="today"),
    pytest.param("now()", "SELECT CURRENT_TIMESTAMP() AS `tmp`", id="now"),
    # Test datetime operations
    create_extract_unary_param("year"),
    create_datetime_unary_param("extract_time", "TIME"),
    create_datetime_unary_param("extract_date", "DATE"),
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
        'format_datetime(when,"%d-%m")',
        QUERY.format("FORMAT_TIMESTAMP('%d-%m', `when`, 'UTC')"),
        id="format_datetime",
    ),
    pytest.param(
        'truncate(when, "ms")',
        QUERY.format("TIMESTAMP_TRUNC(`when`, MILLISECOND)"),
        id="truncate milliseconds from datetime",
    ),
    pytest.param(
        'truncate(birthday, "d")',
        QUERY.format("DATE_TRUNC(`birthday`, DAY)"),
        id="truncate day from date",
    ),
    pytest.param(
        "when - when",
        QUERY.format("TIMESTAMP_DIFF(`when`, `when`, SECOND)"),
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
        'datetime_diff(when, when, "Y")',
        QUERY.format("TIMESTAMP_DIFF(`when`, `when`, YEAR)"),
        id="datetime datetime_diff",
    ),
    pytest.param(
        'datetime_diff(extract_time(when), lunch, "m")',
        QUERY.format("TIME_DIFF(TIME(`when`), `lunch`, MINUTE)"),
        id="time datetime_diff",
    ),
    pytest.param(
        'datetime_diff(extract_date( when), when, "W")',
        QUERY.format("DATE_DIFF(DATE(`when`), `when`, WEEK)"),
        id="date datetime_diff",
    ),
    pytest.param(
        "subtract_days(birthday, 30)",
        QUERY.format("DATE_SUB(`birthday`, INTERVAL 30 DAY)"),
        id="date subtract_days",
    ),
    pytest.param(
        "day_of_week(birthday)",
        QUERY.format("EXTRACT(DAYOFWEEK FROM `birthday`)", id="dat_of_week"),
    ),
    pytest.param(
        "weekday(birthday)",
        "SELECT\n  CASE EXTRACT(DAYOFWEEK FROM `birthday`)\n    WHEN 1 THEN 'Sunday'\n    WHEN 2 THEN 'Monday'\n    WHEN 3 THEN 'Tuesday'\n    WHEN 4 THEN 'Wednesday'\n    WHEN 5 THEN 'Thursday'\n    WHEN 6 THEN 'Friday'\n    WHEN 7 THEN 'Saturday'\n    ELSE CAST(NULL AS STRING)\n  END AS `tmp`\nFROM olympians",
        id="weekday",
    ),
    # Test boolean functions and and or
    pytest.param(
        "and(athlete='Usain Bolt', is_nice, 1=1)",
        QUERY.format("((`athlete` = 'Usain Bolt') AND `is_nice`) AND TRUE"),
        id="and",
    ),
    pytest.param(
        "or(athlete='Usain Bolt', is_nice, 1=1)",
        QUERY.format("((`athlete` = 'Usain Bolt') OR `is_nice`) OR TRUE"),
        id="or",
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
    pytest.param(
        'regex_extract(\'{"id": "1234", "name": "John"}\', \'{"id": "(.*?)",\', 0)',
        'SELECT REGEXP_EXTRACT_ALL(\'{"id": "1234", "name": "John"}\', r\'{"id": "(.*?)",\')[SAFE_OFFSET(0)] AS `tmp`',
        id="regex_extract with quote nesting",
    ),
    pytest.param(
        "to_json_string(biography)",
        QUERY.format("TO_JSON_STRING(`biography`)"),
        id="to_json_string",
    ),
]


@pytest.mark.parametrize("formula, expected_sql", PARAMS)
def test_formula(formula, expected_sql):
    sql = ibis_bigquery.compile(compile_formula(TABLE, formula))
    assert sql == expected_sql


@pytest.mark.parametrize(
    "formula, expected",
    [
        pytest.param(
            '"erratum humanum est"',
            "erratum humanum est",
            id="strings with double quotes",
        ),
        pytest.param(
            "'erratum humanum est'",
            "erratum humanum est",
            id="strings with single quotes",
        ),
    ],
)
def test_string(formula, expected):
    result = compile_formula(TABLE, formula)
    assert result == expected


FUNCTION_NAMES = {func["name"] for func in FUNCTIONS}


def extract_function(param):
    value = param.values[0]
    matches = sorted(
        [function for function in FUNCTION_NAMES if function in value],
        key=len,
        reverse=True,
    )
    if matches:
        return matches[0]
    if "+" in value:
        return "add"
    if "-" in value:
        return "subtract"
    if "/" in value:
        return "divide"
    if "*" in value:
        return "product"
    if "%" in value:
        return "modulo"


def test_all_functions_test():
    test_functions = {extract_function(param) for param in PARAMS}
    assert test_functions == FUNCTION_NAMES
