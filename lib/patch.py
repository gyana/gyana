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


compiler.SelectBuilder._collect_Difference = _collect_Difference

compiler.QueryBuilder.intersect_class = Intersection
compiler.QueryBuilder.difference_class = Difference
