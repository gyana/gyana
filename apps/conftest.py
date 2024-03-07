import os

from apps.base.tests.client import *  # noqa
from apps.base.tests.factory import *  # noqa
from apps.base.tests.fixtures import *  # noqa

pytest_plugins = ("celery.contrib.pytest",)


def pytest_configure():
    # support for playwright https://github.com/microsoft/playwright-python/issues/224
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
