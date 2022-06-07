from functools import singledispatch

from fuzzywuzzy import process
from lark.exceptions import VisitError

from apps.base.core.table_data import get_type_name
from apps.base.core.utils import error_name_to_snake
from apps.base.templates import template_exists
from apps.columns.exceptions import ArgumentError, ColumnAttributeError, ParseError
from apps.columns.transformer import FUNCTIONS, ColumnNotFound, FunctionNotFound
from apps.nodes.models import Node


class CreditException(Exception):
    def __init__(self, node_id, uses_credits) -> None:
        self.node_id = node_id
        self.uses_credits = uses_credits

    @property
    def node(self):
        return Node.objects.get(pk=self.node_id)


class JoinTypeError(Exception):
    def __init__(
        self,
        left_column_type,
        right_column_type,
        left_column_name,
        right_column_name,
        *args,
    ):
        super().__init__(*args)
        self.left_column_type = left_column_type
        self.right_column_type = right_column_type
        self.left_column_name = left_column_name
        self.right_column_name = right_column_name


class NodeResultNone(Exception):
    def __init__(self, node, *args: object) -> None:
        super().__init__(*args)

        self.node = node


class ColumnNamesDontMatch(Exception):
    def __init__(self, index, left_columns, right_columns, *args):
        super().__init__(*args)
        self.index = index
        self.left_columns = left_columns
        self.right_columns = right_columns


@singledispatch
def handle_node_exception(e):

    error_template = f"nodes/errors/{error_name_to_snake(e)}.html"

    return {
        "error_template": error_template
        if template_exists(error_template)
        else "nodes/errors/default.html"
    }


FUNCTION_NAMES = [f["name"] for f in FUNCTIONS]


@handle_node_exception.register(VisitError)
def _(e):
    if isinstance(e.orig_exc, ColumnNotFound):
        suggestion = process.extractOne(e.orig_exc.column, e.orig_exc.columns)
        return {
            "error_template": "nodes/errors/column_not_found.html",
            "column": e.orig_exc.column,
            "suggestion": suggestion[0] if suggestion else None,
        }
    elif isinstance(e.orig_exc, FunctionNotFound):
        suggestion = process.extractOne(e.orig_exc.function, FUNCTION_NAMES)
        return {
            "error_template": "nodes/errors/function_not_found.html",
            "function": e.orig_exc.function,
            "suggestion": suggestion[0] if suggestion else None,
        }
    elif isinstance(e.orig_exc, ArgumentError):
        expected = (
            len(e.orig_exc.function["arguments"])
            if len(e.orig_exc.args) > len(e.orig_exc.function["arguments"])
            else len(
                [f for f in e.orig_exc.function["arguments"] if not f.get("optional")]
            )
        )
        return {
            "error_template": "nodes/errors/argument_error.html",
            "function": e.orig_exc.function["name"],
            "arg_length": len(e.orig_exc.args),
            "expected": expected,
        }
    elif isinstance(e.orig_exc, ColumnAttributeError):
        return {
            "error_template": "nodes/errors/column_attribute_error.html",
            "column": e.orig_exc.column.get_name(),
            "column_type": get_type_name(e.orig_exc.column.type()),
            "function": e.orig_exc.function,
        }
    return {
        "error_template": "nodes/errors/visit_error.html",
        "message": "There was an error in your formula.",
    }


@handle_node_exception.register(JoinTypeError)
def _(e):
    return {
        "error_template": "nodes/errors/join_type_error.html",
        "left_column_type": get_type_name(e.left_column_type),
        "right_column_type": get_type_name(e.right_column_type),
        "right_column_name": e.right_column_name,
        "left_column_name": e.left_column_name,
    }


@handle_node_exception.register(ColumnNamesDontMatch)
def _(e):
    return {
        "error_template": "nodes/errors/columnnames_dont_match.html",
        "left_columns": e.left_columns,
        "right_columns": e.right_columns,
        "index": e.index,
    }


@handle_node_exception.register(ParseError)
def _(e):
    return {
        "error_template": "nodes/errors/parsing_error.html",
        "formula": e.formula,
        "columns": e.columns,
    }
