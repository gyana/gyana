from ibis_bigquery.client import BigQueryClient

from ibis.client import SQLClient

# BigQueryClient is a subclass of SQLClient, and the only addition is to
# rename the partition column which requires an extra API call
# but it is unnecessary for us
BigQueryClient.table = SQLClient.table
