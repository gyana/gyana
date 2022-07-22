from datetime import date
from functools import lru_cache
from unittest.mock import MagicMock, Mock

from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table as BqTable

from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import TABLE_NAME, PickableMock
from apps.nodes._sentiment_utils import (
    DELIMITER,
    SENTIMENT_COLUMN_NAME,
    TEXT_COLUMN_NAME,
)

POSITIVE_SCORE = +0.9
NEGATIVE_SCORE = -0.9

USAIN = "Usain Bolt"
SAKURA = "Sakura Yosozumi"
SENTIMENT_LOOKUP = {
    SAKURA: POSITIVE_SCORE,
    USAIN: NEGATIVE_SCORE,
}  # cache as creating mocks is expensive


@lru_cache(len(SENTIMENT_LOOKUP))
def score_to_sentence_mock(sentence_text: str):
    """Mocks a sentence to place inside an AnalyzeSentimentResponse"""
    sentence = MagicMock()
    sentence.text.content = sentence_text
    sentence.sentiment.score = SENTIMENT_LOOKUP[sentence_text]
    return sentence


def mock_gcp_analyze_sentiment(text, _):
    """Mocks the AnalyzeSentimentResponse sent back from GCP"""
    mocked = MagicMock()

    # covers the scalar case too as scalars are sent over as a single-row column
    mocked.sentences = [score_to_sentence_mock(x) for x in text.split(DELIMITER)]

    return mocked


INPUT_QUERY = f"SELECT *\nFROM `{TABLE_NAME}`"
DEFAULT_X_Y = {"x": 0, "y": 0}


INPUT_DATA = [
    {
        "id": 1,
        "athlete": USAIN,
        "birthday": date(year=1986, month=8, day=21),
    },
    {
        "id": 2,
        "athlete": SAKURA,
        "birthday": date(year=2002, month=3, day=15),
    },
]

DISTINCT_QUERY = "SELECT *\nFROM (\n  SELECT `athlete` AS `text`\n  FROM (\n    SELECT DISTINCT `athlete`\n    FROM `project.dataset.table`\n  ) t1\n) t0\nWHERE `text` IS NOT NULL"


def mock_bq_client_data(bigquery):
    def side_effect(query, **kwargs):
        mock = PickableMock()

        if query == DISTINCT_QUERY:
            mock.rows_dict = [{"text": row["athlete"]} for row in INPUT_DATA]
            mock.total_rows = len(INPUT_DATA)
        elif "EXCEPT DISTINCT" in query:
            mock.rows_dict = []
            mock.total_rows = 0
        else:
            mock.rows_dict = INPUT_DATA
            mock.total_rows = len(INPUT_DATA)
        return mock

    def result(query, **kwargs):
        mock = PickableMock()

        if query == DISTINCT_QUERY:
            mock.result = Mock(
                return_value=[{"text": row["athlete"]} for row in INPUT_DATA]
            )
            mock.total_rows = len(INPUT_DATA)
        elif "EXCEPT DISTINCT" in query:
            mock.result = Mock(return_value=[])
            mock.total_rows = 0
        else:
            mock.result = Mock(return_value=INPUT_DATA)
            mock.total_rows = len(INPUT_DATA)

        return mock

    bigquery.query = Mock(side_effect=result)
    bigquery.get_query_results = Mock(side_effect=side_effect)


def mock_bq_client_schema(bigquery):
    def side_effect(table, **kwargs):
        if table.split(".")[-1].split("_")[0] in [
            "cache",
            "intermediate",
        ]:
            schema = [
                SchemaField(TEXT_COLUMN_NAME, "string"),
                SchemaField(SENTIMENT_COLUMN_NAME, "float"),
            ]
        else:
            schema = [
                SchemaField(column, str(type_))
                for column, type_ in TABLE.schema().items()
            ][:3]
        return BqTable(
            table,
            schema=schema,
        )

    bigquery.get_table = MagicMock(side_effect=side_effect)
