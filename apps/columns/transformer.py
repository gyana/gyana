import json

import ibis
import ibis.expr.datatypes as dt
from lark import Transformer, v_args

from apps.base.core.ibis.compiler import today

from .types import TYPES

with open("apps/columns/functions.json", "r") as file:
    # TODO: Add back
    # * substr
    # * translate
    # * right
    # * left
    # * day_of_week
    data = file.read()

FUNCTIONS = json.loads(data)


def _hash(caller, args):
    return caller.hash("farm_fingerprint")


def convert(caller, args):
    type_ = TYPES[args[0]]
    return caller.cast(type_)


def weekday(caller, args):
    day_of_week = caller.day_of_week()
    return day_of_week.cases(
        [
            (1, "Sunday"),
            (2, "Monday"),
            (3, "Tuesday"),
            (4, "Wednesday"),
            (5, "Thursday"),
            (6, "Friday"),
            (7, "Saturday"),
        ]
    )


def _cast_string(py_scalar_or_column):
    return (
        ibis.literal(py_scalar_or_column).cast(dt.string)
        if isinstance(py_scalar_or_column, int)
        else ibis.cast(py_scalar_or_column, dt.string)
    )


def create_date(caller, args):
    year = _cast_string(caller)
    month = _cast_string(args[0])
    day = _cast_string(args[1])
    text = year + "-" + month + "-" + day
    return text.parse_date("%Y-%m-%d")


def create_time(caller, args):
    hour = _cast_string(caller)
    minute = _cast_string(args[0])
    second = _cast_string(args[1])
    text = hour + ":" + minute + ":" + second
    return text.parse_time("%H:%M:%S")


def and_(caller, args):
    query = caller
    for arg in args:
        query &= arg
    return query


def or_(caller, args):
    query = caller
    for arg in args:
        query |= arg
    return query


ODD_FUNCTIONS = {
    "and": and_,
    "or": or_,
    "hash": _hash,
    "cast": convert,
    "weekday": weekday,
    "create_date": create_date,
    "create_time": create_time,
}

NO_CALLER = {"today": today, "now": ibis.now}


@v_args(inline=True)
class TreeToIbis(Transformer):
    """Evaluates the Lark AST of a formula language sentence into a ibis expression."""

    def __init__(self, query):
        super().__init__()
        self.query = query

    def brackets(self, token):
        return token

    def string(self, token):
        return token.value.strip('"')

    def string_(self, token):
        return token.value.strip("'")

    def column(self, token):
        return self.query[token.value]

    def function(self, token, *args):
        function_name = token.value.lower()
        function = next(filter(lambda f: f["name"] == function_name, FUNCTIONS))
        args = list(args)
        if not args:
            return NO_CALLER[function_name]()
        caller = args.pop(0)
        if isinstance(caller, (int, str, float)):
            caller = ibis.literal(caller)

        if odd_func := ODD_FUNCTIONS.get(function["id"]):
            return odd_func(caller, args)
        func = getattr(caller, function["id"])
        if function["id"] != "coalesce" and any(
            arg.get("repeatable") for arg in function["arguments"]
        ):
            return func(args)
        return func(*args)

    # -----------------------------------------------------------------------
    # Datetimes
    # -----------------------------------------------------------------------

    def datetime(self, date, time):
        return ibis.literal(f"{date}T{time}")

    def date(self, token):
        return ibis.literal(token.value)

    def time(self, token):
        return ibis.literal(token.value)

    # -----------------------------------------------------------------------
    # Numeric
    # -----------------------------------------------------------------------

    @staticmethod
    def lt(left, right):
        return left < right

    @staticmethod
    def gt(left, right):
        return left > right

    @staticmethod
    def ge(left, right):
        return left >= right

    @staticmethod
    def le(left, right):
        return left <= right

    @staticmethod
    def add(left, right):
        return left + right

    @staticmethod
    def subtract(left, right):
        return left - right

    @staticmethod
    def multiply(left, right):
        return left * right

    @staticmethod
    def divide(left, right):
        return left / right

    @staticmethod
    def negate(arg):
        return -arg

    @staticmethod
    def number(token):
        return float(token.value) if "." in token.value else int(token.value)

    @staticmethod
    def modulo(left, right):
        return left % right

    # -----------------------------------------------------------------------
    # Logical
    # -----------------------------------------------------------------------

    @staticmethod
    def true():
        return True

    @staticmethod
    def false():
        return False

    # -----------------------------------------------------------------------
    # Shared
    # -----------------------------------------------------------------------

    @staticmethod
    def eq(left, right):
        return left == right

    @staticmethod
    def ne(left, right):
        return left != right
