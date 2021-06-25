import re

from django import template
from django.template.defaultfilters import register
from django.utils.translation import gettext_lazy as _


# https://stackoverflow.com/a/51090108
@register.filter(name="dict_key")
def dict_key(d, k):
    """Returns the given key from a dictionary."""
    return d.get(k)


# https://djangosnippets.org/snippets/9/
# allows for python expressions in django templates
class ExprNode(template.Node):
    def __init__(self, expr_string, var_name):
        self.expr_string = expr_string
        self.var_name = var_name

    def render(self, context):
        try:
            clist = list(context)
            clist.reverse()
            d = {}
            d["_"] = _
            for c in clist:
                d.update(c)
            if self.var_name:
                context[self.var_name] = eval(self.expr_string, d)
                return ""
            else:
                return str(eval(self.expr_string, d))
        except:
            raise


r_expr = re.compile(r"(.*?)\s+as\s+(\w+)", re.DOTALL)


def do_expr(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires arguments" % token.contents[0]
        )
    m = r_expr.search(arg)
    if m:
        expr_string, var_name = m.groups()
    else:
        if not arg:
            raise template.TemplateSyntaxError(
                "%r tag at least require one argument" % tag_name
            )

        expr_string, var_name = arg, None
    return ExprNode(expr_string, var_name)


do_expr = register.tag("expr", do_expr)
