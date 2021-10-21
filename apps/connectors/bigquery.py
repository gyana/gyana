from apps.base.clients import bigquery_client
from apps.connectors.fivetran.schema import get_bq_datasets_from_schemas


def delete_connector_datasets(connector):
    datasets = get_bq_datasets_from_schemas(connector)

    for dataset in datasets:
        bigquery_client().delete_dataset(
            dataset, delete_contents=True, not_found_ok=True
        )
