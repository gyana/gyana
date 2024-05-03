import ibis
import pytest

from apps.columns.engine import compile_formula
from apps.columns.transformer import FUNCTIONS

FUNC_MAP = {
    "trim": "strip",
    "ltrim": "lstrip",
    "rtrim": "rstrip",
    "extract_time": "time",
    "extract_date": "date",
}


def create_str_unary_param(func_name):
    return pytest.param(
        f"{func_name}(athlete)",
        lambda d: getattr(d.athlete, FUNC_MAP.get(func_name, func_name))(),
        id=func_name,
    )


def create_int_unary_param(func_name):
    return pytest.param(
        f"{func_name}(medals)",
        lambda d: getattr(d.medals, func_name)(),
        id=func_name,
    )


def create_datetime_unary_param(func_name):
    return pytest.param(
        f"{func_name}(when)",
        lambda d: getattr(d.when, FUNC_MAP.get(func_name, func_name))(),
        id=func_name,
    )


def create_extract_unary_param(func_name):
    return pytest.param(
        f"{func_name}(when)",
        lambda d: getattr(d.when, func_name)(),
        id=func_name,
    )


PARAMS = [
    pytest.param(
        "isnull(athlete)",
        lambda d: d.athlete.isnull(),
        id="isnull",
    ),
    pytest.param(
        "notnull(stars)",
        lambda d: d.stars.notnull(),
        id="notnull",
    ),
    pytest.param(
        'fillnull(athlete, "Usain Bolt")',
        lambda d: d.athlete.fillna("Usain Bolt"),
        id="fillnull",
    ),
    pytest.param(
        'convert(medals, "float")',
        lambda d: d.medals.cast("float"),
        id="convert int to float",
    ),
    pytest.param(
        'convert(athlete, "timestamp")',
        lambda d: d.athlete.cast("timestamp"),
        id="convert string to datetime",
    ),
    pytest.param(
        'convert(birthday, "str")',
        lambda d: d.birthday.cast("string"),
        id="convert date to string",
    ),
    pytest.param(
        "coalesce(id, medals, stars)",
        lambda d: d.id.coalesce(d.medals, d.stars),
        id="coalesce",
    ),
    pytest.param(
        "ifelse(is_nice, medals*10, medals-5)",
        lambda d: d.is_nice.ifelse(d.medals * 10, d.medals - 5),
        id="if else",
    ),
    pytest.param(
        'between(athlete, "Rafael Nadal" , "Roger Federer")',
        lambda d: d.athlete.between("Rafael Nadal", "Roger Federer"),
        id="between string column",
    ),
    pytest.param(
        'find(athlete, "Kipchoge")',
        lambda d: d.athlete.find("Kipchoge"),
        id="find no optional arguments",
    ),
    pytest.param(
        "lpad(athlete,3)",
        lambda d: d.athlete.lpad(3),
        id="lpad no optional argument",
    ),
    pytest.param(
        'lpad(athlete,3, "\n")',
        lambda d: d.athlete.lpad(3, "\n"),
        id="lpad with fillchar",
    ),
    pytest.param(
        "hash(athlete)",
        lambda d: d.athlete.hash(),
        id="hash",
    ),
    pytest.param(
        'join(", ", athlete, "that genius")',
        lambda d: ibis.literal(", ").join([d.athlete, "that genius"]),
        id="join",
    ),
    pytest.param(
        'json_extract(\'{"class":{"id": 3}}\', "$.class.id")',
        lambda d: ibis.literal('{"class":{"id": 3}}')
        .cast("json")["class"]["id"]
        .cast("string"),
        id="json_extract",
    ),
    pytest.param(
        "rpad(athlete,3)",
        lambda d: d.athlete.rpad(3),
        id="rpad no optional argument",
    ),
    pytest.param(
        'rpad(athlete,3, "\n")',
        lambda d: d.athlete.rpad(3, "\n"),
        id="rpad with fillchar",
    ),
    pytest.param(
        'like(athlete, "Tom Daley")',
        lambda d: d.athlete.like("Tom Daley"),
        id="like",
    ),
    pytest.param(
        'contains(athlete, "Usain Bolt")',
        lambda d: d.athlete.contains("Usain Bolt"),
        id="contains",
    ),
    pytest.param(
        "repeat(athlete, 2)",
        lambda d: d.athlete.repeat(2),
        id="repeat",
    ),
    pytest.param(
        'regex_extract(athlete, "ough", 2)',
        lambda d: d.athlete.re_extract("ough", 2),
        id="regex_extract",
    ),
    pytest.param(
        'regex_replace(athlete, "ough", "uff")',
        lambda d: d.athlete.re_replace("ough", "uff"),
        id="regex_replace",
    ),
    pytest.param(
        'regex_search(athlete, "Will.*")',
        lambda d: d.athlete.re_search("Will.*"),
        id="regex_search",
    ),
    pytest.param(
        'replace(athlete, "ough", "uff")',
        lambda d: d.athlete.replace("ough", "uff"),
        id="replace",
    ),
    pytest.param(
        'substitute(athlete, "Tim")',
        lambda d: d.athlete.substitute("Tim"),
        id="substitute no optional arguments",
    ),
    pytest.param(
        'substitute(athlete, "Tim", "Tom")',
        lambda d: d.athlete.substitute("Tim", "Tom"),
        id="substitute with replace argument",
    ),
    pytest.param(
        'substitute(athlete, "Tim", "Tom", "Till")',
        lambda d: d.athlete.substitute("Tim", "Tom", "Till"),
        id="substitute with both arguments",
    ),
    pytest.param(
        "left(athlete, 4)",
        lambda d: d.athlete.left(4),
        id="left",
    ),
    pytest.param(
        "right(athlete, 4)",
        lambda d: d.athlete.right(4),
        id="right",
    ),
    pytest.param(
        "parse_date(athlete, '%Y-%m-%d')",
        lambda d: d.athlete.to_timestamp("%Y-%m-%d").date(),
        id="parse_date",
    ),
    pytest.param(
        "parse_time(athlete, '%H:%M:%S')",
        lambda d: d.athlete.to_timestamp("%H:%M:%S").time(),
        id="parse_time",
    ),
    pytest.param(
        "parse_datetime(athlete, '%Y-%m-%dT%H:%M:%S')",
        lambda d: d.athlete.to_timestamp("%Y-%m-%dT%H:%M:%S"),
        id="parse_datetime",
    ),
    pytest.param(
        "add(medals, stars)",
        lambda d: d.medals + d.stars,
        id="add integer and float columns",
    ),
    pytest.param(
        "medals + 5",
        lambda d: d.medals + 5,
        id="add integer scalar to integer column",
    ),
    pytest.param(
        "between(medals,2,10)",
        lambda d: d.medals.between(2, 10),
        id="between integer column",
    ),
    pytest.param(
        "ceiling(medals)",
        lambda d: d.medals.ceil(),
        id="ceil",
    ),
    pytest.param(
        "divide(medals, stars)",
        lambda d: d.medals / d.stars,
        id="div integer and float columns",
    ),
    pytest.param(
        "medals / 42",
        lambda d: d.medals / 42,
        id="div integer column and integer scalar",
    ),
    pytest.param(
        "floor(stars)",
        lambda d: d.stars.floor(),
        id="floor",
    ),
    pytest.param(
        "log(medals, 3)",
        lambda d: d.medals.log(3),
        id="log",
    ),
    pytest.param(
        "log2(medals)",
        lambda d: d.medals.log2(),
        id="log2",
    ),
    pytest.param(
        "product(stars, medals)",
        lambda d: d.stars * d.medals,
        id="multiply int and float column",
    ),
    pytest.param(
        "medals % 3",
        lambda d: d.medals % 3,
        id="modulo integer column and integer scalar",
    ),
    pytest.param(
        "round(stars, 2)",
        lambda d: d.stars.round(2),
        id="round",
    ),
    pytest.param(
        "stars * 42",
        lambda d: d.stars * 42,
        id="multiply float column and int scalar",
    ),
    pytest.param(
        "power(stars, medals)",
        lambda d: d.stars.pow(d.medals),
        id="float column to the power of int column",
    ),
    pytest.param(
        "subtract(stars, medals)",
        lambda d: d.stars - d.medals,
        id="subtract int column from float column",
    ),
    pytest.param(
        "stars - 42.0",
        lambda d: d.stars - 42.0,
        id="subtract float scalar from float column",
    ),
    pytest.param(
        'datetime_seconds(medals, "s")',
        lambda d: d.medals.to_timestamp("s"),
        id="integer column to datetime",
    ),
    pytest.param(
        'datetime_seconds(131313131313, "ms")',
        lambda d: ibis.literal(131313131313).to_timestamp("ms"),
        id="integer to datetime",
    ),
    pytest.param(
        "date(1993,07, medals)",
        lambda d: (
            ibis.literal(1993).cast("string")
            + "-"
            + ibis.literal(7).cast("string")
            + "-"
            + d.medals.cast("string")
        )
        .to_timestamp("%Y-%m-%d")
        .date(),
        id="date",
    ),
    pytest.param(
        "time(12,12, medals)",
        lambda d: (
            ibis.literal(12).cast("string")
            + ":"
            + ibis.literal(12).cast("string")
            + ":"
            + d.medals.cast("string")
        )
        .to_timestamp("%H:%M:%S")
        .time(),
        id="time",
    ),
    pytest.param("today()", lambda d: ibis.now().date(), id="today"),
    pytest.param("now()", lambda d: ibis.now(), id="now"),
    pytest.param(
        "between(birthday, 1990-01-01, 2000-07-01)",
        lambda d: d.birthday.between("1990-01-01", "2000-07-01"),
        id="between date column",
    ),
    pytest.param(
        'format_datetime(when,"%d-%m")',
        lambda d: d.when.strftime("%d-%m"),
        id="format_datetime",
    ),
    pytest.param(
        'truncate(when, "ms")',
        lambda d: d.when.truncate("ms"),
        id="truncate milliseconds from datetime",
    ),
    pytest.param(
        'truncate(birthday, "d")',
        lambda d: d.birthday.truncate("d"),
        id="truncate day from date",
    ),
    pytest.param(
        "when - when",
        lambda d: d.when.delta(d.when, "s"),
        id="datetime difference",
    ),
    pytest.param(
        "birthday - birthday",
        lambda d: d.birthday.delta(d.birthday, "d"),
        id="date difference",
    ),
    pytest.param(
        "lunch - lunch",
        lambda d: d.lunch.delta(d.lunch, "s"),
        id="time difference",
    ),
    pytest.param(
        'datetime_diff(when, when, "Y")',
        lambda d: d.when.delta(d.when, "Y"),
        id="datetime datetime_diff",
    ),
    pytest.param(
        'datetime_diff(extract_time(when), lunch, "m")',
        lambda d: d.when.time().delta(d.lunch, "m"),
        id="time datetime_diff",
    ),
    pytest.param(
        'datetime_diff(extract_date( when), birthday, "W")',
        lambda d: d.when.date().delta(d.birthday, "W"),
        id="date datetime_diff",
    ),
    pytest.param(
        "subtract_days(birthday, 30)",
        lambda d: d.birthday - ibis.interval(30, unit="D"),
        id="date subtract_days",
    ),
    pytest.param(
        "day_of_week(birthday)",
        lambda d: d.birthday.day_of_week.index(),
        id="day_of_week",
    ),
    pytest.param(
        "weekday(birthday)",
        lambda d: d.birthday.day_of_week.full_name(),
        id="weekday",
    ),
    pytest.param(
        "and(athlete='Usain Bolt', is_nice, 1=1)",
        lambda d: (d.athlete == "Usain Bolt") & d.is_nice & (1 == 1),
        id="and",
    ),
    pytest.param(
        "or(athlete='Usain Bolt', is_nice, 1=1)",
        lambda d: (d.athlete == "Usain Bolt") | d.is_nice | (1 == 1),
        id="or",
    ),
    pytest.param(
        "(medals + stars)/(stars - 42) * medals",
        lambda d: ((d.medals + d.stars) / (d.stars - 42)) * d.medals,
        id="arithmetic formula mixing different operation",
    ),
    pytest.param(
        'upper(replace(athlete, "ff", "f"))',
        lambda d: d.athlete.replace("ff", "f").upper(),
        id="nest two string methods",
    ),
    pytest.param(
        "round(exp(month(birthday)*medals))",
        lambda d: (d.birthday.month() * d.medals).exp().round(),
        id="nest numeric and datetime operations",
    ),
    pytest.param(
        'ifelse(between(birthday, 2000-01-01, 2000-01-31), "millenium kid", "normal kid")',
        lambda d: d.birthday.between("2000-01-01", "2000-01-31").ifelse(
            "millenium kid", "normal kid"
        ),
        id="nest ifelse with datetime function",
    ),
    pytest.param(
        'regex_extract(\'{"id": "1234", "name": "John"}\', \'{"id": "(.*?)",\', 0)',
        lambda d: ibis.literal('{"id": "1234", "name": "John"}').re_extract(
            '{"id": "(.*?)",', 0
        ),
        id="regex_extract with quote nesting",
    ),
    create_str_unary_param("lower"),
    create_str_unary_param("upper"),
    create_str_unary_param("length"),
    create_str_unary_param("reverse"),
    create_str_unary_param(
        "trim",
    ),
    create_str_unary_param("ltrim"),
    create_str_unary_param("rtrim"),
    create_int_unary_param("abs"),
    create_int_unary_param("exp"),
    create_int_unary_param("sqrt"),
    create_int_unary_param("ln"),
    create_int_unary_param("log10"),
    create_extract_unary_param("year"),
    create_datetime_unary_param("extract_time"),
    create_datetime_unary_param("extract_date"),
    create_extract_unary_param("second"),
    create_extract_unary_param("month"),
    create_extract_unary_param("minute"),
    create_extract_unary_param("millisecond"),
    create_extract_unary_param("hour"),
    create_datetime_unary_param("epoch_seconds"),
    create_extract_unary_param("day"),
]


@pytest.mark.parametrize("formula, get_expected", PARAMS)
def test_formula(engine, formula, get_expected):
    query = compile_formula(engine.data, formula)
    assert query.equals(get_expected(engine.data))


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
def test_string(formula, expected, engine):
    result = compile_formula(engine.data, formula)
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
