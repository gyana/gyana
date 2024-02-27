import pytest


@pytest.fixture
def sheets():
    pass


@pytest.fixture
def drive_v2():
    pass


@pytest.fixture
def bigquery():
    pass


@pytest.fixture(scope="session")
def celery_config():
    return {"broker_url": "redis://localhost:6379/1", "result_backend": "django-db"}
