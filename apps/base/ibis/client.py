from ibis_bigquery.client import BigQueryClient, rename_partitioned_column

import ibis.expr.schema as sch


def table(self, name, database=None):
    # a single query for bigquery
    project, dataset = self._parse_project_and_dataset(database)
    table_ref = self.client.dataset(dataset, project=project).table(name)
    bq_table = self.client.get_table(table_ref)

    # conn.get_schema(...)
    schema = sch.infer(bq_table)

    # SQLClient: conn.table(...)
    qualified_name = self._fully_qualified_name(name, database)
    node = self.table_class(qualified_name, schema, self)
    t = self.table_expr_class(node)

    # BigQueryClient: conn.table(...)
    rename_partitioned_column(t, bq_table, self.partition_column)

    return t


# By default, the Ibis client makes 2 requests to BigQuery
# - for the schema in conn.get_schema(...)
# - for the table partition information in conn.table(...)
# This refactors the logic into a single function, with one API call.
BigQueryClient.table = table
