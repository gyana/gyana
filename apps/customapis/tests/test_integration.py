import json

import pytest
import requests
from celery import states
from django.core import mail
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.integrations.models import Integration

pytestmark = pytest.mark.django_db


def base_formset(formset):
    return {
        f"{formset}-TOTAL_FORMS": 0,
        f"{formset}-MIN_NUM_FORMS": 1000,
        f"{formset}-MAX_NUM_FORMS": 1000,
        f"{formset}-INITIAL_FORMS": 0,
    }


QUERY_PARAMS_BASE_DATA = base_formset("queryparams")
HTTP_HEADERS_BASE_DATA = base_formset("httpheaders")

TEST_JSON = {
    "products": [
        {"name": "neera", "started": 2016},
        {"name": "vayu", "started": 2019},
        {"name": "gyana", "started": 2021},
    ]
}


@pytest.fixture
def request_safe(mocker):
    # request response with content manually set to json
    request_safe = mocker.patch("apps.customapis.requests.request.request_safe")
    response = requests.Response()
    response._content = json.dumps(TEST_JSON).encode("utf-8")
    response.status_code = 200
    request_safe.return_value = response
    return request_safe


def test_customapi_create(client, logged_in_user, project, bigquery, request_safe):

    # mock the configuration
    bigquery.load_table_from_uri().exception = lambda: False
    bigquery.reset_mock()  # reset the call count

    LIST = f"/projects/{project.id}/integrations"

    # test: create a new customapi, configure it and complete the sync

    # create
    r = client.get(f"{LIST}/customapis/new")
    assertOK(r)
    assertFormRenders(r, ["name", 'is_scheduled'])

    r = client.post(f"{LIST}/customapis/new", data={"name": "JSON todos"})

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
            *QUERY_PARAMS_BASE_DATA.keys(),
            *HTTP_HEADERS_BASE_DATA.keys(),
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
            **QUERY_PARAMS_BASE_DATA,
            **HTTP_HEADERS_BASE_DATA,
        },
    )
    assertRedirects(r, f"{DETAIL}/load", target_status_code=302)
    customapi.refresh_from_db()

    # validate the request
    assert request_safe.call_count == 1
    assert len(request_safe.call_args.args) == 1
    assert isinstance(request_safe.call_args.args[0], requests.Session)
    assert request_safe.call_args.kwargs == {
        "method": "GET",
        "url": "https://json.url",
        "params": {},
        "headers": {},
    }

    # validate the generated JSON file
    assert customapi.ndjson_file.file.read().splitlines() == [
        json.dumps(item).encode("utf-8") for item in TEST_JSON["products"]
    ]

    # validate the bigquery load job
    assert bigquery.load_table_from_uri.call_count == 1
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
