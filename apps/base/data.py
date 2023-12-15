from apps.base.engine import get_backend_client


def copy_table(from_table, to_table):
    """Copies a bigquery table from `from_table` to `to_table.

    Replaces if the table already exists, mostly important to work locally,
    in prod that shouldn't be necessary.
    """
    return get_backend_client().create_or_replace_table(
        to_table, f"SELECT * FROM {from_table}"
    )
