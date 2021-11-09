from apps.base import clients


def query_to_gcs(query, gcs_path):
    client = clients.bigquery()
    # Create temporary table in bigquery
    job = client.query(query)
    job.result()

    # Use temporary table and export to GCS
    extract_job = client.extract_table(job.destination, gcs_path)
    extract_job.result()
