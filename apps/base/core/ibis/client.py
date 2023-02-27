import ibis
from ibis.backends.base.sql import BaseSQLBackend

# The Ibis BigQuery client makes 2 requests to BigQuery
# - for the schema in conn.get_schema(...)
# - for the table partition information in conn.table(...)
# native connectors are not partitioned, and fivetran documentation suggests
# by default connectors are not partitioned either, better to remove for now
# https://fivetran.com/docs/destinations/bigquery/partition-table#converttopartitionedtables
# Backend.get_schema = BaseSQLBackend.get_schema

original_table = BaseSQLBackend.table


def table(self, name, database=None):
    self.set_database(database)
    return original_table(self, name, database)


ibis.bigquery.table = table
