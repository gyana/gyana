import json
from uuid import uuid4

import requests
from celery import shared_task
from django.utils import timezone
from jsonpath_ng import parse

from apps.runs.models import JobRun
from apps.users.models import CustomUser

from .models import Sheet


@shared_task(bind=True)
def run_api_sync_task(self, run_id):
    run = JobRun.objects.get(pk=run_id)
    integration = run.integration
    custom_api = integration.custom_api

    # fetch data from the api
    response = requests.get(custom_api.url).json()
    jsonpath_expr = parse(custom_api.json_path)
    data = jsonpath_expr.find(response)[0].value
    ndjson = "\n".join([json.dumps(item) for item in data])

    # write to GCS
    custom_api.ndjson_file.save(custom_api.integration.name, ndjson)

    # run the BigQuery load job


def run_api_sync(sheet: Sheet, user: CustomUser, skip_up_to_date=False):
    run = JobRun.objects.create(
        source=JobRun.Source.INTEGRATION,
        integration=sheet.integration,
        task_id=uuid4(),
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
        user=user,
    )
    run_api_sync_task.apply_async(
        (run.id,), {"skip_up_to_date": skip_up_to_date}, task_id=str(run.task_id)
    )
