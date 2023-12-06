from apps.base import clients


def copy_table(from_table, to_table):
    """Copies a bigquery table from `from_table` to `to_table.

    Replaces if the table already exists, mostly important to work locally,
    in prod that shouldn't be necessary.
    """
    client = clients.get_backend_client().client

    return client.raw_sql(
        f"CREATE OR REPLACE TABLE {to_table} as (SELECT * FROM {from_table})"
    )
