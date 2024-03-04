import pytest
from django.db import connection


@pytest.fixture(autouse=True)
def patches():
    pass


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


@pytest.fixture(autouse=True)
def reset_sequences():
    yield
    with connection.cursor() as cursor:
        cursor.execute(
            """DO $$
DECLARE
    row record;
BEGIN
    FOR row IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public'
    LOOP
        EXECUTE 'ALTER SEQUENCE ' || quote_ident(row.sequence_name) || ' RESTART WITH 1';
    END LOOP;
END $$;"""
        )
