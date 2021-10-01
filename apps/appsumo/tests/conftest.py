from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def patches(*_):
    with patch("analytics.track"):
        with patch("apps.base.analytics.identify_user"):
            yield


@pytest.fixture(autouse=True)
def patch_bigquery(*_):
    with patch("apps.base.clients.bigquery_client"):
        yield
