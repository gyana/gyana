import json
from itertools import chain
from uuid import uuid4

import requests
from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.template.loader import get_template
from django.utils import timezone
from jsonpath_ng import parse
from requests_oauthlib import OAuth2Session

from apps.base.clients import get_engine
from apps.base.core.bigquery import sanitize_bq_column_name
from apps.base.core.utils import catchtime
from apps.integrations.emails import send_integration_ready_email
from apps.runs.models import JobRun
from apps.tables.models import Table
from apps.users.models import CustomUser

from .models import CustomApi
from .requests import request
from .requests.authorization import get_authorization
from .requests.body import get_body


def sanitize_nested_fields(d):
    if isinstance(d, list):
        return [sanitize_nested_fields(f) for f in d]
    if isinstance(d, dict):
        return {
            sanitize_bq_column_name(k): sanitize_nested_fields(v) for k, v in d.items()
        }
    return d


@shared_task(bind=True, time_limit=request.REQUEST_TIMEOUT)
def run_customapi_sync_task(self, run_id):
    run = JobRun.objects.get(pk=run_id)
    integration = run.integration
    customapi = integration.customapi

    # render the error template with debug context
    context = {}

    try:
        # fetch data from the api, extract the list of items, write to GCS as
        # newline delimited JSON
        session = (
            OAuth2Session(
                token=customapi.oauth2.token,
                auto_refresh_url=customapi.oauth2.token_url,
            )
            if customapi.authorization == CustomApi.Authorization.OAUTH2
            else requests.Session()
        )
        get_authorization(session, customapi)
        body = get_body(session, customapi)
        response = request.request_safe(
            session,
            method=customapi.http_request_method,
            url=customapi.url,
            params={q.key: q.value for q in customapi.queryparams.all()},
            headers={h.key: h.value for h in customapi.httpheaders.all()},
            **body,
        )

        context["response"] = response
        response.raise_for_status()

        try:
            data = response.json()
        except json.JSONDecodeError:
            raise Exception("Unable to parse the response to JSON.")

        context["json"] = json.dumps(data, indent=2)

        jsonpath_expr = parse(customapi.json_path)
        jsonpath_matches = jsonpath_expr.find(data)

        if len(jsonpath_matches) == 0:
            raise Exception(
                "JSONPath expression does not match any part of the JSON response."
            )

        # Merge results for JSON Path expression with multiple matches
        # e.g. airtable API $.records[*].fields
        parsed_data = list(
            chain.from_iterable(
                match.value if isinstance(match.value, list) else [match.value]
                for match in jsonpath_matches
            )
        )

        # bigquery does not automatically sanitize
        sanitized_data = sanitize_nested_fields(parsed_data)

        ndjson = "\n".join([json.dumps(item) for item in sanitized_data])
        customapi.ndjson_file.save(
            f"customapi_{customapi.id}.ndjson", ContentFile(ndjson.encode("utf-8"))
        )

        context["ndjson"] = ndjson
        context["ndjson_file"] = customapi.ndjson_file

    except Exception as exc:
        raise Exception(
            get_template("customapis/_error.html").render(
                context={"message": str(exc), **context}
            )
        )

    # we need to save the table instance to get the PK from database, this ensures
    # database will rollback automatically if there is an error with the bigquery
    # table creation, avoids orphaned table entities

    with transaction.atomic():
        table, created = Table.objects.get_or_create(
            integration=integration,
            source=Table.Source.INTEGRATION,
            name=customapi.table_id,
            namespace=integration.project.team.tables_dataset_id,
            project=integration.project,
        )

        with catchtime() as get_time_to_sync:
            get_engine().import_table_from_customapi(table=table, customapi=customapi)

        table.sync_metadata_from_source()

    if created:
        send_integration_ready_email(integration, int(get_time_to_sync()))

    return integration.id


def run_customapi_sync(customapi: CustomApi, user: CustomUser):
    run = JobRun.objects.create(
        source=JobRun.Source.INTEGRATION,
        integration=customapi.integration,
        task_id=uuid4(),
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
        user=user,
    )
    run_customapi_sync_task.apply_async((run.id,), task_id=str(run.task_id))
