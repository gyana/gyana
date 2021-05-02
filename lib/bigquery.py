from functools import lru_cache

import google.auth
from django.conf import settings
from google.cloud import bigquery


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


def query_sheet(id, sheet_url):
    client = bigquery_client()

    # https://cloud.google.com/bigquery/external-data-drive#python
    external_config = bigquery.ExternalConfig("GOOGLE_SHEETS")
    external_config.source_uris = [sheet_url]
    external_config.autodetect = True
    table_id = f"temporary_{id}"
    job_config = bigquery.QueryJobConfig(table_definitions={table_id: external_config})
    sql = "SELECT * FROM `{}` LIMIT 100".format(table_id)

    return client.query(sql, job_config=job_config).to_dataframe()
