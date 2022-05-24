import pytest

from apps.base.tests.client import *  # noqa
from apps.base.tests.factory import *  # noqa
from apps.base.tests.fixtures import *  # noqa


@pytest.fixture(autouse=True)
def override_settings(settings):
    settings.CACHEOPS_ENABLED = False
