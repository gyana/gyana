import json

import pytest
import requests
from celery import states
from django.core import mail
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.integrations.models import Integration

pytestmark = pytest.mark.django_db


def base_formset(formset):
    return {
        f"{formset}-TOTAL_FORMS": 0,
        f"{formset}-MIN_NUM_FORMS": 1000,
        f"{formset}-MAX_NUM_FORMS": 1000,
        f"{formset}-INITIAL_FORMS": 0,
    }


fields = [
    "url",
    "json_path",
    "http_request_method",
    "authorization",
    "api_key_key",
    "api_key_value",
    "api_key_add_to",
    "bearer_token",
    "username",
    "password",
    "oauth2",
    "body",
    "body_raw",
    "body_binary",
]

QUERY_PARAMS_BASE_DATA = base_formset("queryparams")
HTTP_HEADERS_BASE_DATA = base_formset("httpheaders")
FORM_URL_ENCODED_ENTRIES_BASE_DATA = base_formset("formurlencodedentries")
FORM_DATA_ENCODED_ENTRIES_BASE_DATA = base_formset("formdataentries")


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


def test_customapi_create(
    client, logged_in_user, project, load_table_from_uri, mock_bq_query, request_safe
):

    LIST = f"/projects/{project.id}/integrations"

    # test: create a new customapi, configure it and complete the sync

    # create
    r = client.get(f"{LIST}/customapis/new")
    assertOK(r)
    assertFormRenders(r, ["name", "is_scheduled"])

    r = client.post(
        f"{LIST}/customapis/new", data={"name": "JSON todos", "is_scheduled": False}
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
            *fields,
            *QUERY_PARAMS_BASE_DATA.keys(),
            *HTTP_HEADERS_BASE_DATA.keys(),
            *FORM_URL_ENCODED_ENTRIES_BASE_DATA.keys(),
            *FORM_DATA_ENCODED_ENTRIES_BASE_DATA.keys(),
        ],
    )

    assert request_safe.call_count == 0
    assert mock_bq_query.call_count == 0

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
            **QUERY_PARAMS_BASE_DATA,
            **HTTP_HEADERS_BASE_DATA,
            **FORM_URL_ENCODED_ENTRIES_BASE_DATA,
            **FORM_DATA_ENCODED_ENTRIES_BASE_DATA,
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
    assert load_table_from_uri.call_count == 1
    table = integration.table_set.first()
    assert load_table_from_uri.call_args.args == (
        customapi.gcs_uri,
        table.fqn,
    )
    job_config = load_table_from_uri.call_args.kwargs["job_config"]
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
