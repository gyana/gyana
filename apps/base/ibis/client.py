from ibis_bigquery.client import BigQueryClient

from ibis.client import SQLClient

# The Ibis BigQuery client makes 2 requests to BigQuery
# - for the schema in conn.get_schema(...)
# - for the table partition information in conn.table(...)
# native connectors are not partitioned, and fivetran documentation suggests
# by default connectors are not partitioned either, better to remove for now
# https://fivetran.com/docs/destinations/bigquery/partition-table#converttopartitionedtables
BigQueryClient.table = SQLClient.table
