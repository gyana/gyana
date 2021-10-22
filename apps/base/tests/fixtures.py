from unittest.mock import MagicMock

import pytest
import waffle
from apps.base import clients
from apps.teams.models import Team
from apps.users.models import CustomUser
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

    # the test client does not have host header by default
    mocker.patch("apps.cnames.middleware.HostMiddleware", BlankMiddleware)

    settings.GS_BUCKET_NAME = "gyana-test"

    yield


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
