from functools import lru_cache

import google.auth
import ibis_bigquery
from django.conf import settings
from django.utils.text import slugify
from google.cloud import bigquery
from googleapiclient import discovery

SLUG = slugify(settings.CLOUD_NAMESPACE)
DATASET_ID = f"{SLUG}_integrations"
DATAFLOW_ID = f"{SLUG}_dataflows"


def get_credentials():
    return google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ]
    )


@lru_cache
def sheets_client():
    credentials, _ = get_credentials()

    return discovery.build("sheets", "v4", credentials=credentials)


@lru_cache
def bigquery_client():
    # https://cloud.google.com/bigquery/external-data-drive#python
    credentials, project = get_credentials()

    # return bigquery.Client(project=settings.GCP_PROJECT)
    return bigquery.Client(
        credentials=credentials, project=project, location=settings.BIGQUERY_LOCATION
    )


@lru_cache
def ibis_client():
    return ibis_bigquery.connect(
        project_id=settings.GCP_PROJECT, auth_external_data=True, dataset_id=DATASET_ID
    )
