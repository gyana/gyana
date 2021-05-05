from datetime import datetime
from functools import lru_cache

import google.auth
import ibis_bigquery
from apps.datasets.models import Dataset
from apps.filters.models import Filter
from django.conf import settings
from django.forms.widgets import Widget
from google.cloud import bigquery

DATASET_ID = "datasets"
DEFAULT_LIMIT = 10


@lru_cache
def bigquery_client():

    # https://cloud.google.com/bigquery/external-data-drive#python
    credentials, project = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ]
    )

    # return bigquery.Client(project=settings.GCP_PROJECT)
    return bigquery.Client(credentials=credentials, project=project)


@lru_cache
def ibis_client():
    return ibis_bigquery.connect(
        project_id=settings.GCP_PROJECT, auth_external_data=True, dataset_id=DATASET_ID
    )


def sync_table(dataset: Dataset):

    client = bigquery_client()

    client.query(
        f"CREATE OR REPLACE TABLE {DATASET_ID}.{dataset.table_id} AS SELECT * FROM {DATASET_ID}.{dataset.external_table_id}"
    ).result()

    if not dataset.has_initial_sync:
        dataset.has_initial_sync = True
    dataset.last_synced = datetime.now()
    dataset.save()


def create_external_table(dataset: Dataset):

    client = bigquery_client()

    bq_dataset = client.get_dataset(DATASET_ID)

    external_table = bigquery.Table(bq_dataset.table(dataset.external_table_id))

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

    external_table.external_data_configuration = external_config
    external_table = client.create_table(external_table, exists_ok=True)


def query_dataset(dataset: Dataset):

    if not dataset.has_initial_sync:
        create_external_table(dataset)
        sync_table(dataset)

    conn = ibis_client()
    table = conn.table(dataset.table_id)

    return conn.execute(table.limit(DEFAULT_LIMIT))


def query_widget(widget: Widget):

    conn = ibis_client()
    table = conn.table(widget.dataset.table_id)

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


def get_columns(dataset: Dataset):
    client = bigquery_client()

    bq_table = client.get_table(f"{DATASET_ID}.{dataset.table_id}")

    return bq_table.schema
