import pytest
from celery.contrib.testing import worker
from django.db import connection
from pandas import read_csv

from apps.base.clients import get_engine

BIGQUERY_TIMEOUT = 20000
SHARED_SHEET = "https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit"

fixtures = "apps/base/tests/e2e/fixtures"


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
def engine():
    pass


@pytest.fixture(scope="session")
def celery_config():
    return {"broker_url": "redis://localhost:6379/1", "result_backend": "django-db"}


# fork of original celery.contrib.pytest.celery_worker to use celery_session_app
@pytest.fixture()
def celery_worker(celery_session_app):
    with worker.start_worker(celery_session_app, pool="solo") as w:
        yield w


# reset sequences after each test, enables us to hard-code primary keys
# adds ~1s latency per e2e test
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


@pytest.fixture(autouse=True)
def seed_engine(settings):

    settings_dict = connection.settings_dict

    user = settings_dict["USER"]
    password = settings_dict["PASSWORD"]
    host = settings_dict["HOST"]
    port = settings_dict["PORT"]
    database = settings_dict["NAME"]

    # force engine to use same test database for simplicity
    settings.ENGINE_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    with connection.cursor() as cursor:
        cursor.execute("""CREATE SCHEMA IF NOT EXISTS cypress_team_000001_tables""")

        engine = get_engine()
        df = read_csv(f"{fixtures}/store_info.csv")
        engine._df_to_sql(df, "upload_000000001", "cypress_team_000001_tables")
        engine._df_to_sql(df, "output_node_000000002", "cypress_team_000001_tables")
