from itertools import chain

from google.api_core.exceptions import NotFound

from apps.base import clients
from apps.connectors.fivetran.config import ServiceTypeEnum

FIVETRAN_SYSTEM_TABLES = {"fivetran_audit", "fivetran_audit_warning"}


def delete_connector_datasets(connector):

    for dataset in connector.fivetran_datasets | connector.synced_datasets:
        clients.bigquery().delete_dataset(
            dataset, delete_contents=True, not_found_ok=True
        )


def _get_bq_tables_from_dataset_safe(dataset_id, enabled_table_ids=None):

    # fetch all tables in a dataset and return empty set if does not exist
    # this is useful for the fivetran schema logic as not all the schemas and
    # tables reported by fivetran may actually be created in bigquery

    try:
        bq_tables = list(clients.bigquery().list_tables(dataset_id))
        if enabled_table_ids is None:
            return [t for t in bq_tables if t.table_id not in FIVETRAN_SYSTEM_TABLES]
        return [t for t in bq_tables if t.table_id in enabled_table_ids]
    except NotFound:
        return set()


def _get_bq_table_safe(biqquery_id):
    try:
        return clients.bigquery().get_table(biqquery_id)
    except NotFound:
        return


def get_bq_tables_for_connector(connector):

    # definitive function to map from a fivetran connector to one or more
    # bigquery schemas with one or more tables
    #
    # an empty return indicates that there is no data in bigquery yet
    #
    # for api_cloud and database, we take the intersection of what fivetran says
    # it will create vs what bigquery reports was actually created, this:
    #
    # - filters out tables that are incorrectly included in bigquery - e.g.
    #   failed deletions or fivetran system tables
    # - filters out tables that fivetran expected, but weren't created in
    #   bigquery - e.g. if the source app does not contain any of that entity

    service_type = connector.conf.service_type

    # one dataset, multiple dynamic tables
    if service_type == ServiceTypeEnum.EVENT_TRACKING:
        return _get_bq_tables_from_dataset_safe(connector.schema)

    # one dataset, one fixed table
    if service_type in [ServiceTypeEnum.WEBHOOKS, ServiceTypeEnum.REPORTING_API]:
        bq_table = _get_bq_table_safe(connector.schema)
        return {bq_table} if bq_table is not None else set()

    # one dataset, multiple fixed tables determined by schema
    if service_type == ServiceTypeEnum.API_CLOUD:
        if not (schemas := connector.schema_obj.schemas):
            return set()
        return _get_bq_tables_from_dataset_safe(
            connector.schema,
            enabled_table_ids=schemas[0].enabled_table_ids,
        )

    # multiple datasets, multiple fixed tables determined by schema
    bq_table_generator = (
        _get_bq_tables_from_dataset_safe(
            # database connectors have multiple bigquery datasets and use a schema prefix
            f"{connector.schema}_{schema.name_in_destination}",
            schema.enabled_table_ids,
        )
        for schema in connector.schema_obj.enabled_schemas
    )
    return set(chain(*bq_table_generator))
