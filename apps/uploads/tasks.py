import time
from functools import reduce

from apps.base.clients import DATASET_ID
from apps.integrations.bigquery import sync_table
from apps.integrations.models import Integration
from apps.tables.models import Table
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from google.api_core.exceptions import GoogleAPICallError


@shared_task(bind=True)
def file_sync(self, file: str, project_id: int):
    """
    Task syncs a file into bigquery. On success it

    :returns: Tuple(table.id, elapsed_time)
    """
    # 1. Create table to track progress in
    table = Table(
        source=Table.Source.INTEGRATION,
        bq_dataset=DATASET_ID,
        project_id=project_id,
        num_rows=0,
    )
    table.save()

    # We keep track of timing
    sync_start_time = time.time()

    # 2. Sync the file into BigQuery
    sync_generator = sync_table(table=table, file=file, kind=Integration.Kind.CSV)
    query_job = next(sync_generator)

    # 3. Record progress on the sync
    progress_recorder = ProgressRecorder(self)

    def calc_progress(jobs):
        return reduce(
            lambda tpl, curr: (
                # We only keep track of completed states for now, not failed states
                tpl[0] + (1 if curr.status == "COMPLETE" else 0),
                tpl[1] + 1,
            ),
            jobs,
            (0, 0),
        )

    while query_job.running():
        current, total = calc_progress(query_job.query_plan)
        progress_recorder.set_progress(current, total)
        time.sleep(0.5)

    progress_recorder.set_progress(*calc_progress(query_job.query_plan))

    # 4. Let the rest of the generator run, if the sync is successful this yields.
    # Otherwise it raises
    try:
        next(sync_generator)
    except (GoogleAPICallError, TimeoutError) as e:
        # If our bigquery sync failed we also delete the table to avoid dangling entities
        table.delete()
        raise e

    sync_end_time = time.time()

    return (table.id, int(sync_end_time - sync_start_time))
