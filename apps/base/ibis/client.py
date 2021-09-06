from ibis_bigquery.client import BigQueryClient

import ibis.expr.schema as sch
from ibis.client import SQLClient


def table(self, name, database=None):
    # a single query for bigquery
    project, dataset = self._parse_project_and_dataset(database)
    table_ref = self.client.dataset(dataset, project=project).table(name)
    bq_table = self.client.get_table(table_ref)

    # conn.get_schema(...)
    schema = sch.infer(bq_table)

    # conn.table(...)
    qualified_name = self._fully_qualified_name(name, database)
    schema = self._get_table_schema(qualified_name)
    node = self.table_class(qualified_name, schema, self)
    tbl = self.table_expr_class(node)

    # attach the bq_table for usage downstream
    tbl.bq_table = bq_table

    return tbl


# BigQueryClient is a subclass of SQLClient, and the only addition is to
# rename the partition column which requires an extra API call
# but it is unnecessary for us
BigQueryClient.table = SQLClient.table
