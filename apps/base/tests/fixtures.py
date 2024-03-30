import os
from unittest.mock import MagicMock

import pytest
import waffle
from django.db import connection
from django.http import HttpResponse
from django.urls import get_resolver, path
from pytest_django import live_server_helper
from waffle.templatetags import waffle_tags

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
