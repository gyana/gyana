import datetime as dt

import jwt
import pandas as pd
import pytest
from google.cloud.bigquery import Client
from google.cloud.bigquery.schema import SchemaField
from google.oauth2.service_account import Credentials
from ibis.backends.bigquery import Backend
from ibis.expr.operations import DatabaseTable
from ibis.expr.operations.relations import Namespace

from apps.base.clients import get_engine

from .mock_data import MOCK_SCHEMA


class MockEngine:
    def __init__(self, mocker):
        self.mocker = mocker
        mocker.patch(
            "ibis.backends.bigquery.pydata_google_auth.default",
            return_value=(None, "project"),
        )
        signer = mocker.MagicMock()
        signer.key_id = jwt.encode({"project": "credentials"}, "key_id")
        mocker.patch(
            "google.auth.default",
            return_value=(
                Credentials(jwt.encode({"project": "credentials"}, "key_id"), "", ""),
                "project",
            ),
        )
        mocker.patch(
            "ibis.backends.bigquery.pydata_google_auth.default",
            return_value=(None, "project"),
        )
        query_result = mocker.MagicMock()
        query_result.to_dataframe.return_value = pd.DataFrame()
        query_result.total_rows = 2

        self.data = DatabaseTable(
            name="table",
            namespace=Namespace(schema="project.dataset"),
            schema=MOCK_SCHEMA,
            source=get_engine().client,
        ).to_expr()
        self.create_dataset = mocker.patch.object(Client, "create_dataset")
        self.delete_table = mocker.patch.object(Client, "delete_table")

        self.table = mocker.patch.object(Backend, "table", return_value=self.data)
        self._make_session = (mocker.patch.object(Backend, "_make_session"),)
        self.query_and_wait = mocker.patch.object(
            Client, "query_and_wait", return_value=query_result
        )
        self.raw_sql = mocker.patch.object(Backend, "raw_sql")

        load_job = mocker.MagicMock()
        load_job.exception = lambda: False
        self.load_table_from_uri = mocker.patch.object(
            Client, "load_table_from_uri", return_value=load_job
        )

        table = mocker.MagicMock()
        table.schema = [
            SchemaField("string_field_0", "STRING"),
            SchemaField("string_field_1", "STRING"),
        ]
        table.modified = dt.datetime(2020, 1, 1)
        table.num_rows = 2
        mocker.patch.object(Client, "get_table", return_value=table)
        query = mocker.MagicMock()
        result = mocker.MagicMock()
        result.values.return_value = ["Name", "Age"]
        query.result.return_value = [result]
        query.exception.return_value = False
        self.query = mocker.patch.object(Client, "query", return_value=query)

    def set_data(self, data):
        return self.mocker.patch.object(Backend, "execute", return_value=data)


@pytest.fixture(autouse=True)
def engine(mocker, settings):
    settings.ENGINE_URL = "bigquery://project"
    return MockEngine(mocker)
