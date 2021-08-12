import json

import ibis
from lark import Transformer, v_args

with open("apps/columns/functions.json", "r") as file:
    data = file.read()

FUNCTIONS = json.loads(data)


@v_args(inline=True)
class TreeToIbis(Transformer):
    """Evaluates the Lark AST of a formula language sentence into a ibis expression."""

    def __init__(self, query):
        super().__init__()
        self.query = query

    def string(self, token):
        return ibis.literal(token.value)

    def brackets(self, token):
        return token

    def string(self, token):
        return ibis.literal(token.value.strip('"'))

    def column(self, token):
        return self.query[token.value]

    def function(self, token, *args):
        args = list(args)
        caller = args.pop(0)
        function_name = token.value.lower()
        function = next(filter(lambda f: f["name"] == function_name, FUNCTIONS))
        func = getattr(caller, function["id"])
        if "..." in function["arguments"]:
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
        if "." in token.value:
            return float(token.value)
        return int(token.value)

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
