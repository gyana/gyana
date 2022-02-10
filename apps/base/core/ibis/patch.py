import ibis.expr.datatypes as dt
from ibis.backends.base.sql import compiler
from ibis.backends.base.sql.compiler import query_builder
from ibis.backends.base.sql.compiler.base import SetOp
from ibis_bigquery.client import _DTYPE_TO_IBIS_TYPE
from ibis_bigquery.datatypes import TypeTranslationContext, ibis_type_to_bigquery_type


class Intersection(SetOp):
    def _get_keyword_list(self):
        return ["INTERSECT DISTINCT"] * (len(self.tables) - 1)


class Difference(SetOp):
    def _get_keyword_list(self):
        return ["EXCEPT DISTINCT"] * (len(self.tables) - 1)


query_builder.Intersection = Intersection
query_builder.Difference = Difference

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
