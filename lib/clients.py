from functools import lru_cache

import google.auth
import ibis.expr.rules as rlz
import ibis_bigquery
from django.conf import settings
from django.utils.text import slugify
from google.cloud import bigquery
from googleapiclient import discovery
from ibis.expr.operations import Arg, ValueOp
from ibis.expr.types import StringValue
from ibis_bigquery import BigQueryExprTranslator

SLUG = slugify(settings.CLOUD_NAMESPACE)
DATASET_ID = f"{SLUG}_integrations"
DATAFLOW_ID = f"{SLUG}_dataflows"


def get_credentials():
    return google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ]
    )


@lru_cache
def sheets_client():
    credentials, _ = get_credentials()

    return discovery.build("sheets", "v4", credentials=credentials)


@lru_cache
def bigquery_client():
    # https://cloud.google.com/bigquery/external-data-drive#python
    credentials, project = get_credentials()

    # return bigquery.Client(project=settings.GCP_PROJECT)
    return bigquery.Client(
        credentials=credentials, project=project, location=settings.BIGQUERY_LOCATION
    )


@lru_cache
def ibis_client():
    return ibis_bigquery.connect(
        project_id=settings.GCP_PROJECT, auth_external_data=True, dataset_id=DATASET_ID
    )


class StartsWith(ValueOp):
    value = Arg(rlz.string)
    start_string = Arg(rlz.string)
    output_type = rlz.shape_like("value", "bool")


def startswith(value, start_string):
    return StartsWith(value, start_string).to_expr()


StringValue.startswith = startswith


compiles = BigQueryExprTranslator.compiles


@compiles(StartsWith)
def _startswith(t, expr):
    # pull out the arguments to the expression
    value, start_string = expr.op().args
    # compile the argument
    t_value = t.translate(value)
    t_start = t.translate(start_string)
    # return a SQLAlchemy expression that calls into the SQLite julianday function
    return f"STARTS_WITH({t_value}, {t_start})"


class EndsWith(ValueOp):
    value = Arg(rlz.string)
    end_string = Arg(rlz.string)
    output_type = rlz.shape_like("value", "bool")


def endswith(value, start_string):
    return EndsWith(value, start_string).to_expr()


StringValue.endswith = endswith


compiles = BigQueryExprTranslator.compiles


@compiles(EndsWith)
def _endswith(t, expr):
    # pull out the arguments to the expression
    value, start_string = expr.op().args
    # compile the argument
    t_value = t.translate(value)
    t_start = t.translate(start_string)
    # return a SQLAlchemy expression that calls into the SQLite julianday function
    return f"ENDS_WITH({t_value}, {t_start})"
