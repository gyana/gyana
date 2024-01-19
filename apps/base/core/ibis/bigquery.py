import beeline
import pandas as pd
from google.cloud import bigquery as bq
from ibis.backends.bigquery import Backend
from ibis.backends.bigquery.client import BigQueryCursor

# update the default execute implemention of Ibis BigQuery backend
# - support the faster synchronous client.query_and_wait
# - include `total_rows` information in pandas results


class DummyQuery:
    def __init__(self, row_iterator):
        self.row_iterator = row_iterator

    def result(self):
        return self.row_iterator


def _execute(self, stmt, results=True, query_parameters=None):
    # run a synchronous query and retrieve results in one API call
    # https://github.com/googleapis/python-bigquery/pull/1722
    job_config = bq.QueryJobConfig(query_parameters=query_parameters or [])
    query_results = self.client.query_and_wait(
        stmt, job_config=job_config, project=self.billing_project
    )
    return BigQueryCursor(DummyQuery(query_results))


@beeline.traced(name="bigquery_query_results_fast")
def execute(self, expr, params=None, limit="default", **kwargs):
    kwargs.pop("timecontext", None)
    query_ast = self.compiler.to_ast_ensure_limit(expr, limit, params=params)
    sql = query_ast.compile()
    self._log(sql)
    cursor = self.raw_sql(sql, params=params, **kwargs)
    schema = self.ast_schema(query_ast, **kwargs)
    result = self.fetch_from_cursor(cursor, schema)

    if hasattr(getattr(query_ast, "dml", query_ast), "result_handler"):
        result = query_ast.dml.result_handler(result)

    if isinstance(result, pd.DataFrame):
        # TODO: find a more elegant solution
        # bypass the default `__setattr__` of `pd.DataFrame`
        result.__dict__["total_rows"] = cursor.query.result().total_rows

    return result


Backend._execute = _execute
Backend.execute = execute
