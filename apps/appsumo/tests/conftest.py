from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def patches(*_):
    with patch("analytics.track"):
        with patch("apps.base.analytics.identify_user"):
            yield
