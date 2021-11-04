from unittest.mock import MagicMock

import ibis.expr.schema as sch
import pytest
import waffle
from apps.base import clients
from apps.teams.models import Team
from apps.users.models import CustomUser
from django.utils import timezone
from ibis_bigquery.client import rename_partitioned_column
from waffle.templatetags import waffle_tags


class BlankMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


@pytest.fixture(autouse=True)
def patches(mocker, settings):
    mocker.patch("analytics.track")
    mocker.patch("apps.base.analytics.identify_user")

    # enable beta
    # https://waffle.readthedocs.io/en/v0.9/testing-waffles.html
    mocker.patch.object(waffle, "flag_is_active", return_value=True)
    mocker.patch.object(waffle_tags, "flag_is_active", return_value=True)

    # run celery tasks within the same thread synchronously
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    # all the clients are mocked
    settings.MOCK_REMOTE_OBJECT_DELETION = False

    # explicitly enable in the test
    settings.ACCOUNT_EMAIL_VERIFICATION = "optional"

    settings.GS_BUCKET_NAME = "gyana-test"

    # the test client host header
    settings.CNAME_ALLOWED_HOSTS = ["testserver"]

    yield


def bind(instance, name, func):
    setattr(
        instance,
        name,
        func.__get__(instance, instance.__class__),
    )


def mock_ibis_client_table(self, name, database):
    t = super(self.__class__).__get__(self).table(name, database=database)
    project, dataset, name = t.op().name.split(".")
    bq_table = self.client.get_table(f"{project}.{dataset}.{name}")
    return rename_partitioned_column(t, bq_table, self.partition_column)


def mock_ibis_client_get_schema(self, name, database):
    project, dataset = self._parse_project_and_dataset(database)
    bq_table = self.client.get_table(f"{project}.{dataset}.{name}")
    return sch.infer(bq_table)


@pytest.fixture(autouse=True)
def bigquery(mocker, settings):
    client = MagicMock()
    # manually override the ibis client with a mock instead
    # set the project name to "project" in auto-generated SQL
    settings.GCP_PROJECT = "project"
    mocker.patch(
        "ibis_bigquery.pydata_google_auth.default", return_value=(None, "project")
    )
    mocker.patch("apps.base.clients.bigquery", return_value=client)
    mocker.patch("ibis_bigquery.client.bq.Client", return_value=client)
    ibis_client = clients.ibis_client()
    ibis_client.client = client

    bind(
        ibis_client,
        "table",
        mock_ibis_client_table,
    )
    bind(
        ibis_client,
        "get_schema",
        mock_ibis_client_get_schema,
    )

    client.get_table().num_rows = 10
    client.get_table().modified = timezone.now()

    yield client


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


@pytest.fixture(autouse=True)
def fivetran(mocker, settings):
    settings.MOCK_FIVETRAN = False
    client = MagicMock()
    mocker.patch("apps.base.clients.fivetran", return_value=client)
    yield client


@pytest.fixture(autouse=True)
def heroku(mocker):
    client = MagicMock()
    mocker.patch("apps.base.clients.heroku", return_value=client)
    yield client


@pytest.fixture
def logged_in_user(client):
    team = Team.objects.create(name="Vayu")
    user = CustomUser.objects.create_user("test", onboarded=True)
    team.members.add(user, through_defaults={"role": "admin"})
    client.force_login(user)
    return user
