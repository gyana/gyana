from datetime import datetime

from apps.datasets.models import Dataset
from apps.filters.models import Filter
from apps.tables.models import Table
from apps.widgets.models import Widget
from django.conf import settings
from django.db import transaction
from google.cloud import bigquery

from lib.clients import DATASET_ID, bigquery_client, ibis_client

DEFAULT_LIMIT = 10


def sync_table(dataset: Dataset, external_table_id: str):

    client = bigquery_client()

    table_id = f"table_{dataset.pk}"

    external_config = create_external_config(dataset)
    job_config = bigquery.QueryJobConfig(
        table_definitions={external_table_id: external_config}
    )

    client.query(
        f"CREATE OR REPLACE TABLE {DATASET_ID}.{table_id} AS SELECT * FROM {DATASET_ID}.{external_table_id}",
        job_config=job_config,
    ).result()

    with transaction.atomic():

        try:
            dataset.table
        except Table.DoesNotExist:
            table = Table(
                bq_table=table_id,
                bq_dataset=DATASET_ID,
                project=dataset.project,
                dataset=dataset,
            )
            table.save()

        dataset.last_synced = datetime.now()
        dataset.save()


def create_external_config(dataset: Dataset):
    if dataset.kind == Dataset.Kind.GOOGLE_SHEETS:
        # https://cloud.google.com/bigquery/external-data-drive#python
        external_config = bigquery.ExternalConfig("GOOGLE_SHEETS")
        external_config.source_uris = [dataset.url]
    elif dataset.kind == Dataset.Kind.CSV:
        external_config = bigquery.ExternalConfig("CSV")
        external_config.source_uris = [
            f"gs://{settings.GS_BUCKET_NAME}/{dataset.file.name}"
        ]

    external_config.autodetect = True

    return external_config


def create_external_table(dataset: Dataset) -> str:

    client = bigquery_client()
    external_table_id = f"table_{dataset.pk}_external"

    bq_dataset = client.get_dataset(DATASET_ID)

    external_table = bigquery.Table(bq_dataset.table(external_table_id))

    external_config = create_external_config(dataset)

    external_table.external_data_configuration = external_config
    external_table = client.create_table(external_table, exists_ok=True)

    return external_table_id


def query_dataset(dataset: Dataset):

    try:
        dataset.table
    except Table.DoesNotExist:
        external_table_id = create_external_table(dataset)
        sync_table(dataset, external_table_id)

    conn = ibis_client()
    table = conn.table(dataset.table.bq_table)

    return conn.execute(table.limit(DEFAULT_LIMIT))


def query_widget(widget: Widget):

    conn = ibis_client()

    table = widget.table.get_query()

    for filter in widget.filter_set.all():
        if filter.type == Filter.Type.INTEGER:
            if filter.integer_predicate == Filter.IntegerPredicate.EQUAL:
                table = table[table[filter.column] == filter.integer_value]
            elif filter.integer_predicate == Filter.IntegerPredicate.EQUAL:
                table = table[table[filter.column] != filter.integer_value]
        elif filter.type == Filter.Type.STRING:
            if filter.string_predicate == Filter.StringPredicate.STARTSWITH:
                table = table[table[filter.column].str.startswith(filter.string_value)]
            elif filter.string_predicate == Filter.StringPredicate.ENDSWITH:
                table = table[table[filter.column].str.endswith(filter.string_value)]

    return conn.execute(table.group_by(widget.label).count(widget.value))


def get_columns(source):
    return source.get_schema()
