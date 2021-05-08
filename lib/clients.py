from functools import lru_cache

import google.auth
import ibis_bigquery
from django.conf import settings
from google.cloud import bigquery

DATASET_ID = "datasets"
DATAFLOW_ID = "dataflows"


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
    return bigquery.Client(
        credentials=credentials, project=project, location=settings.BIGQUERY_LOCATION
    )


@lru_cache
def ibis_client():
    return ibis_bigquery.connect(
        project_id=settings.GCP_PROJECT, auth_external_data=True, dataset_id=DATASET_ID
    )
