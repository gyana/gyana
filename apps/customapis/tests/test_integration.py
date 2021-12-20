import json
from datetime import datetime
from unittest.mock import Mock

import googleapiclient
import pytest
import requests
from celery import states
from django.core import mail
from pytest_django.asserts import (
    assertContains,
    assertFormError,
    assertNotContains,
    assertRedirects,
)

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.integrations.models import Integration

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_safe(mocker):
    # request response with content manually set to json
    request_safe = mocker.patch("apps.customapis.requests.request.request_safe")
    response = requests.Response()
    response._content = json.dumps(
        {"products": [{"neera": 2016, "vayu": 2019, "gyana": 2021}]}
    ).encode("utf-8")
    response.status_code = 200
    request_safe.return_value = response
    return request_safe


def test_customapi_create(client, logged_in_user, project, bigquery, request_safe):

    LIST = f"/projects/{project.id}/integrations"

    # test: create a new customapi, configure it and complete the sync

    # create
    r = client.get(f"{LIST}/customapis/new")
    assertOK(r)
    assertFormRenders(r, ["name", "url"])

    r = client.post(
        f"{LIST}/customapis/new", data={"name": "JSON todos", "url": "https://json.url"}
    )

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.CUSTOMAPI
    assert integration.customapi is not None
    assert integration.created_by == logged_in_user

    customapi = integration.customapi
    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"

    assertRedirects(r, f"{DETAIL}/configure", status_code=303)

    # configure
    r = client.get(f"{DETAIL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(
        r,
        [
            "name",
            "url",
            "json_path",
            "http_request_method",
            "authorization",
            "body",
            "queryparams-TOTAL_FORMS",
            "queryparams-INITIAL_FORMS",
            "queryparams-MIN_NUM_FORMS",
            "queryparams-MAX_NUM_FORMS",
            "httpheaders-TOTAL_FORMS",
            "httpheaders-INITIAL_FORMS",
            "httpheaders-MIN_NUM_FORMS",
            "httpheaders-MAX_NUM_FORMS",
        ],
    )

    assert request_safe.call_count == 0
    assert bigquery.query.call_count == 0

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(
        f"{DETAIL}/configure",
        data={
            "url": "https://json.url",
            "json_path": "$.products",
            "http_request_method": "GET",
            "authorization": "no_auth",
            "body": "none",
            "submit": True,
            "queryparams-TOTAL_FORMS": 0,
            "queryparams-INITIAL_FORMS": 0,
            "queryparams-MIN_NUM_FORMS": 0,
            "queryparams-MAX_NUM_FORMS": 0,
            "httpheaders-TOTAL_FORMS": 0,
            "httpheaders-INITIAL_FORMS": 0,
            "httpheaders-MIN_NUM_FORMS": 0,
            "httpheaders-MAX_NUM_FORMS": 0,
        },
    )
    assertRedirects(r, f"{DETAIL}/load", status_code=303)

    assert request_safe.call_count == 1
    assert bigquery.query.call_count == 1

    # validate the request
    assert request_safe.call_args.args == (requests.Session(),)
    assert request_safe.call_args.kwargs == {
        "method": "GET",
        "url": "https://json.url",
        "params": {},
        "headers": {},
    }

    # validate the generated JSON file
    # todo

    # validate the bigquery load job
    table = integration.table_set.first()
    assert bigquery.load_table_from_uri.call_args.args == (
        customapi.gcs_uri,
        table.bq_id,
    )
    job_config = bigquery.load_table_from_uri.call_args.kwargs["job_config"]
    assert job_config.source_format == "NEWLINE_DELIMITED_JSON"
    assert job_config.write_disposition == "WRITE_TRUNCATE"
    assert job_config.autodetect

    assertRedirects(r, f"{DETAIL}/load", target_status_code=302)

    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    # validate the run and task result exist
    assert integration.runs.count() == 1
    run = integration.runs.first()
    assert run.result is not None
    assert run.result.status == states.SUCCESS

    assert len(mail.outbox) == 1
