from lib.clients import ibis_client


def get_query_from_table(table):

    conn = ibis_client()
    return conn.table(table.bq_table, database=table.bq_dataset)


def get_query_from_integration(integration):

    from apps.integrations.models import Integration

    conn = ibis_client()
    if integration.kind == Integration.Kind.FIVETRAN:
        return conn.table(integration.table_id, database=integration.schema)
    return conn.table(integration.table_id)
