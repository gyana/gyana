from functools import singledispatch

from lark.exceptions import VisitError

from apps.base.core.utils import error_name_to_snake
from apps.base.templates import template_exists
from apps.columns.transformer import ColumnNotFound, FunctionNotFound
from apps.nodes.models import Node


class CreditException(Exception):
    def __init__(self, node_id, uses_credits) -> None:
        self.node_id = node_id
        self.uses_credits = uses_credits

    @property
    def node(self):
        return Node.objects.get(pk=self.node_id)


class JoinTypeError(Exception):
    def __init__(self, left_column, right_column, *args):
        super().__init__(*args)
        self.left_column = left_column
        self.right_column = right_column


class NodeResultNone(Exception):
    def __init__(self, node, *args: object) -> None:
        super().__init__(*args)

        self.node = node


@singledispatch
def handle_node_exception(e):

    error_template = f"nodes/errors/{error_name_to_snake(e)}.html"

    return {
        "error_template": error_template
        if template_exists(error_template)
        else "nodes/errors/default.html"
    }


@handle_node_exception.register(VisitError)
def _(e):
    if isinstance(e.orig_exc, ColumnNotFound):
        message = f"Column {e.orig_exc.column} does not exist on input."
    elif isinstance(e.orig_exc, FunctionNotFound):
        message = f"Function {e.orig_exc.function} does not exist."
    return {
        "error_template": "nodes/errors/visit_error.html",
        "message": message,
    }


@handle_node_exception.register(JoinTypeError)
def _(e):
    return {
        "error_template": "nodes/errors/visit_error.html",
        "left_column": e.left_column,
        "right_column": e.right_column,
    }
