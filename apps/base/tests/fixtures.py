from unittest.mock import MagicMock, patch

import pytest
import waffle
from apps.base.clients import ibis_client
from apps.teams.models import Team
from apps.users.models import CustomUser
from waffle.templatetags import waffle_tags


@pytest.fixture(autouse=True)
def patches(*_):
    with patch("analytics.track"):
        with patch("apps.base.analytics.identify_user"):
            yield


@pytest.fixture(autouse=True)
def bigquery_client(*_):
    client = MagicMock()
    with patch("apps.base.clients.bigquery_client", return_value=client):
        ibis_client().client = client
        yield client


@pytest.fixture(autouse=True)
def sheets_client(*_):
    client = MagicMock()
    with patch("apps.base.clients.sheets_client", return_value=client):
        yield client


@pytest.fixture(autouse=True)
def drive_v2_client(*_):
    client = MagicMock()
    with patch("apps.base.clients.drive_v2_client", return_value=client):
        yield client


@pytest.fixture(autouse=True)
def fivetran_client(*_, settings):
    settings.MOCK_FIVETRAN = False
    client = MagicMock()
    with patch("apps.base.clients.fivetran", return_value=client):
        yield client


@pytest.fixture
def logged_in_user(client):
    team = Team.objects.create(name="team_team")
    user = CustomUser.objects.create_user("test", onboarded=True)
    team.members.add(user, through_defaults={"role": "admin"})
    client.force_login(user)
    return user


@pytest.fixture(autouse=True)
def celery_eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


class BlankMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


@pytest.fixture(autouse=True)
def cname_middleware():
    # the test client does not have host header by default
    with patch("apps.cnames.middleware.HostMiddleware", BlankMiddleware):
        yield


@pytest.fixture(autouse=True)
def enable_beta():
    # https://waffle.readthedocs.io/en/v0.9/testing-waffles.html
    with patch.object(waffle, "flag_is_active", return_value=True):
        with patch.object(waffle_tags, "flag_is_active", return_value=True):
            yield
