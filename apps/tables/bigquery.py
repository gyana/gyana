from lib.clients import ibis_client


def get_query_from_table(table):

    conn = ibis_client()
    return conn.table(table.bq_table, database=table.bq_dataset)
