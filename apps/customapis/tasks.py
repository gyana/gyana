import json
from uuid import uuid4

import requests
from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from jsonpath_ng import parse

from apps.base.time import catchtime
from apps.integrations.emails import send_integration_ready_email
from apps.runs.models import JobRun
from apps.tables.models import Table
from apps.users.models import CustomUser

from .bigquery import import_table_from_customapi
from .models import CustomApi


@shared_task(bind=True)
def run_customapi_sync_task(self, run_id):
    run = JobRun.objects.get(pk=run_id)
    integration = run.integration
    customapi = integration.customapi

    # fetch data from the api, extract the list of items, write to GCS as
    # newline delimited JSON
    # todo:
    # - timeouts and max size for request
    # - validate status code and share error information if failed
    # - validate jsonpath_expr works and print json if failed
    response = requests.get(customapi.url).json()
    jsonpath_expr = parse(customapi.json_path)
    data = jsonpath_expr.find(response)[0].value
    ndjson = "\n".join([json.dumps(item) for item in data])
    customapi.ndjson_file.save(
        f"customapi_{customapi.id}.ndjson", ContentFile(ndjson.encode("utf-8"))
    )

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    with transaction.atomic():

        table, created = Table.objects.get_or_create(
            integration=integration,
            source=Table.Source.INTEGRATION,
            bq_table=customapi.table_id,
            bq_dataset=integration.project.team.tables_dataset_id,
            project=integration.project,
        )

        with catchtime() as get_time_to_sync:
            import_table_from_customapi(table=table, customapi=customapi)

        table.sync_updates_from_bigquery()

    if created:
        send_integration_ready_email(integration, int(get_time_to_sync()))

    return integration.id


def run_customapi_sync(customapi: CustomApi, user: CustomUser, skip_up_to_date=False):
    run = JobRun.objects.create(
        source=JobRun.Source.INTEGRATION,
        integration=customapi.integration,
        task_id=uuid4(),
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
        user=user,
    )
    run_customapi_sync_task.apply_async((run.id,), task_id=str(run.task_id))
