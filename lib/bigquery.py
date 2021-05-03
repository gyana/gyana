from functools import lru_cache

import google.auth
import ibis_bigquery
from apps.datasets.models import Dataset
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
        project_id=settings.GCP_PROJECT, auth_external_data=True
    )


def create_external_table(dataset: Dataset):

    client = bigquery_client()

    bq_dataset = client.get_dataset(DATASET_ID)
    table_id = f"table_{dataset.id}"

    table = bigquery.Table(bq_dataset.table(table_id))

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

    table.external_data_configuration = external_config
    table = client.create_table(table, exists_ok=True)

    dataset.table_id = table_id
    dataset.save()


def query_sheet(dataset: Dataset):

    if dataset.table_id is None:
        create_external_table(dataset)

    conn = ibis_client()
    table = conn.table(dataset.table_id, database=DATASET_ID)

    return conn.execute(table.limit(DEFAULT_LIMIT))


def query_widget(widget: Widget):

    conn = ibis_client()
    table = conn.table(widget.dataset.table_id, database=DATASET_ID)

    return conn.execute(table.group_by(widget.label).count(widget.value))
