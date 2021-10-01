from unittest.mock import patch

import pytest

from apps.teams.models import Team
from apps.users.models import CustomUser


@pytest.fixture(autouse=True)
def patches(*_):
    with patch("analytics.track"):
        with patch("apps.base.analytics.identify_user"):
            yield


@pytest.fixture(autouse=True)
def patch_bigquery(*_):
    with patch("apps.base.clients.bigquery_client"):
        yield


@pytest.fixture
def logged_in_user(client):
    team = Team.objects.create(name="team_team")
    user = CustomUser.objects.create_user("test")
    team.members.add(user, through_defaults={"role": "admin"})
    client.force_login(user)
    return user


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
