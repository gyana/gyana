import beeline
import pandas as pd
from google.cloud import bigquery as bq
from ibis.backends.bigquery import Backend
from ibis.backends.bigquery.client import BigQueryCursor

# update the default execute implemention of Ibis BigQuery backend
# - support the faster synchronous client.query_and_wait
# - include `total_rows` information in pandas results


@beeline.traced(name="bigquery_query_results_fast")
def execute(self, expr, params=None, limit="default", **kwargs):
    sql = expr.compile()

    # run a synchronous query and retrieve results in one API call
    # https://github.com/googleapis/python-bigquery/pull/1722
    job_config = bq.QueryJobConfig()
    query_results = self.client.query_and_wait(
        sql, job_config=job_config, project=self.billing_project, max_results=limit
    )

    df = query_results.to_dataframe()

    if isinstance(df, pd.DataFrame):
        # TODO: find a more elegant solution
        # bypass the default `__setattr__` of `pd.DataFrame`
        df.__dict__["total_rows"] = query_results.total_rows

    return df


Backend.execute = execute
