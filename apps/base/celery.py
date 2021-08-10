from apps.base.clients import BIGQUERY_JOB_LIMIT
from django.utils import timezone

import celery


def is_bigquery_task_running(task_id: str, started: timezone):
    # infer whether a celery task running bigquery job is running

    if task_id is None:
        return False

    # Celery PENDING does not distinguish pending versus tasks auto-cleared after 24 hours
    # https://stackoverflow.com/a/38267978/15425660
    # BigQuery jobs cannot last longer than 6 hours
    # PROGRESS is a custom state from celery-progress
    result = celery.result.AsyncResult(str(task_id))
    elapsed_time = timezone.now() - started

    return (
        result.status in ("PENDING", "PROGRESS")
        and elapsed_time.total_seconds() < BIGQUERY_JOB_LIMIT
    )
