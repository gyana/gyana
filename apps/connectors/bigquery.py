from itertools import chain

from apps.base.clients import bigquery_client, fivetran_client
from apps.connectors.config import get_services
from apps.connectors.models import Connector


def get_bq_tables_from_connector(connector: Connector):

    client = bigquery_client()

    service_conf = get_services()[connector.service]

    if service_conf["requires_schema_prefix"] == "t":
        schemas = (
            schema.name_in_destination
            for schema in fivetran_client().get_schemas(connector)
        )
        tables = (
            client.list_tables(f"{connector.schema}_{schema}") for schema in schemas
        )
        bq_tables = chain(*tables)
    else:
        bq_tables = client.list_tables(connector.schema)

    return [t for t in bq_tables if t.table_id != "fivetran_audit"]
