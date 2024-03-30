import os

from apps.base.tests.client import *  # noqa
from apps.base.tests.engine import *  # noqa
from apps.base.tests.factory import *  # noqa
from apps.base.tests.fixtures import *  # noqa


def pytest_configure():
    # support for playwright https://github.com/microsoft/playwright-python/issues/224
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
