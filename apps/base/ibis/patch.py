from ibis_bigquery.client import _DTYPE_TO_IBIS_TYPE
from ibis_bigquery.datatypes import TypeTranslationContext, ibis_type_to_bigquery_type

import ibis.expr.datatypes as dt
from ibis.backends.base_sqlalchemy import compiler
from ibis.backends.base_sqlalchemy.compiler import SetOp


class Intersection(SetOp):
    def _get_keyword_list(self):
        return ["INTERSECT DISTINCT"] * (len(self.tables) - 1)


class Difference(SetOp):
    def _get_keyword_list(self):
        return ["EXCEPT DISTINCT"] * (len(self.tables) - 1)


def _collect_Difference(self, expr, toplevel=False):
    if toplevel:
        raise NotImplementedError()


def _collect_Intersection(self, expr, toplevel=False):
    if toplevel:
        raise NotImplementedError()


compiler.SelectBuilder._collect_Difference = _collect_Difference
compiler.SelectBuilder._collect_Intersection = _collect_Intersection


compiler.QueryBuilder.intersect_class = Intersection
compiler.QueryBuilder.difference_class = Difference

_DTYPE_TO_IBIS_TYPE["BIGNUMERIC"] = dt.Decimal(76, 38)


@ibis_type_to_bigquery_type.register(dt.Decimal, TypeTranslationContext)
def trans_numeric(t, context):
    if (t.precision, t.scale) == (38, 9):
        return "NUMERIC"
    if (t.precision, t.scale) == (76, 38):
        return "BIGNUMERIC"
    raise TypeError(
        """BigQuery only supports the NUMERIC decimal types 
with a precision of 38 and scale of 9 and the BIGNUMERIC decimal type 
with a precision of 76 and 38 """
    )
