from lib.bigquery import ibis_client


def get_input_query(node):
    conn = ibis_client()
    return conn.table(node._input_dataset.table_id)


NODE_FROM_CONFIG = {"input": get_input_query}
