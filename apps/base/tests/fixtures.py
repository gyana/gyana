import datetime as dt
import os
from unittest.mock import MagicMock

import pandas as pd
import pytest
import waffle
from django.db import connection
from django.http import HttpResponse
from django.urls import get_resolver, path
from google.cloud.bigquery import Client
from google.cloud.bigquery.schema import SchemaField
from ibis.backends.bigquery import Backend
from ibis.expr.operations import DatabaseTable
from ibis.expr.operations.relations import Namespace
from pytest_django import live_server_helper
from waffle.templatetags import waffle_tags

from apps.base.clients import get_engine
from apps.base.tests.mock_data import MOCK_SCHEMA
from apps.teams.models import Team
from apps.users.models import CustomUser

from .playwright import PlaywrightForm


class BlankMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


@pytest.fixture
def with_pg_trgm_extension():
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    yield


@pytest.fixture(autouse=True)
def patches(mocker, settings):
    settings.TEST = True

    mocker.patch("analytics.track")
    mocker.patch("apps.base.analytics.identify_user")

    # enable beta
    # https://waffle.readthedocs.io/en/v0.9/testing-waffles.html
    mocker.patch.object(waffle, "flag_is_active", return_value=True)
    mocker.patch.object(waffle_tags, "flag_is_active", return_value=True)

    # disable celery progress
    mocker.patch("celery_progress.backend.ProgressRecorder")

    # run celery tasks within the same thread synchronously
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.CELERY_TASK_STORE_EAGER_RESULT = True

    # all the clients are mocked
    settings.MOCK_REMOTE_OBJECT_DELETION = False

    # explicitly enable in the test
    settings.ACCOUNT_EMAIL_VERIFICATION = "optional"

    settings.GS_BUCKET_NAME = "gyana-test"

    # use filesystem instead of google cloud storage
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

    yield


def bind(instance, name, func):
    setattr(
        instance,
        name,
        func.__get__(instance, instance.__class__),
    )


def mock_backend_client_get_schema(self, name):
    table = self.client.get_table(name)
    return sch.infer(table)


@pytest.fixture(autouse=True)
def mock_bigquery(mocker):
    query_result = mocker.MagicMock()
    query_result.to_dataframe.return_value = pd.DataFrame()
    query_result.total_rows = 2
    return dict(
        table=mocker.patch.object(
            Backend,
            "table",
            return_value=DatabaseTable(
                name="table",
                namespace=Namespace(schema="project.dataset"),
                schema=MOCK_SCHEMA,
                source=get_engine().client,
            ).to_expr(),
        ),
        _make_session=mocker.patch.object(Backend, "_make_session"),
        query_and_wait=mocker.patch.object(
            Client, "query_and_wait", return_value=query_result
        ),
        raw_sql=mocker.patch.object(Backend, "raw_sql"),
    )


@pytest.fixture
def load_table_from_uri(mocker):
    # mock the configuration
    load_job = mocker.MagicMock()
    load_job.exception = lambda: False
    return mocker.patch.object(Client, "load_table_from_uri", return_value=load_job)


@pytest.fixture
def mock_bq_query(mocker):
    table = mocker.MagicMock()
    table.schema = [
        SchemaField("string_field_0", "STRING"),
        SchemaField("string_field_1", "STRING"),
    ]
    table.modified = dt.datetime(2020, 1, 1)
    table.num_rows = 2
    mocker.patch.object(Client, "get_table", return_value=table)
    query = mocker.MagicMock()
    result = mocker.MagicMock()
    result.values.return_value = ["Name", "Age"]
    query.result.return_value = [result]
    query.exception.return_value = False
    return mocker.patch.object(Client, "query", return_value=query)


@pytest.fixture(autouse=True)
def sheets(mocker):
    client = MagicMock()
    mocker.patch("apps.base.clients.sheets", return_value=client)
    yield client


@pytest.fixture(autouse=True)
def drive_v2(mocker):
    client = MagicMock()
    mocker.patch("apps.base.clients.drive_v2", return_value=client)
    yield client


@pytest.fixture
def user():
    team = Team.objects.create(name="Vayu")
    user = CustomUser.objects.create_user(
        "test", email="test@gyana.com", onboarded=True
    )
    team.members.add(user, through_defaults={"role": "member"})
    return user


@pytest.fixture
def logged_in_user(client):
    team = Team.objects.create(name="Vayu")
    user = CustomUser.objects.create_user(
        "test", email="test@gyana.com", onboarded=True
    )
    team.members.add(user, through_defaults={"role": "admin"})
    client.force_login(user)
    return user


@pytest.fixture
def project(project_factory, logged_in_user):
    return project_factory(team=logged_in_user.teams.first())


@pytest.fixture
def dynamic_view(settings):
    url_patterns = get_resolver(settings.ROOT_URLCONF).url_patterns
    original_urlconf_len = len(url_patterns)

    def _dynamic_view(content):
        if isinstance(content, str):

            def view_func(request):
                return HttpResponse(content)

            temporary_urls = [
                path("test-dynamic-view", view_func, name="test-dynamic-view"),
            ]
        else:
            temporary_urls = content

        get_resolver(settings.ROOT_URLCONF).url_patterns += temporary_urls
        return "test-dynamic-view"

    yield _dynamic_view

    get_resolver(settings.ROOT_URLCONF).url_patterns = url_patterns[
        :original_urlconf_len
    ]


# duplicate of pytest_django live_server but using SimpleTestCase instead of TransactionTestCase
# search for "live_server" (with quotes) in pytest_django to understand why this works
@pytest.fixture(scope="session")
def live_server_js(request: pytest.FixtureRequest):
    addr = (
        request.config.getvalue("liveserver")
        or os.getenv("DJANGO_LIVE_TEST_SERVER_ADDRESS")
        or "localhost"
    )

    server = live_server_helper.LiveServer(addr)
    yield server
    server.stop()


@pytest.fixture
def pwf(page, dynamic_view, live_server_js):
    return PlaywrightForm(page, dynamic_view, live_server_js)
