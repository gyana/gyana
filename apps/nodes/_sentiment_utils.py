from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Iterator, List, Tuple

import numpy as np
import pandas as pd
from apps.base import clients
from apps.nodes.models import Node
from apps.tables.models import Table
from apps.teams.models import CreditTransaction
from celery.app import shared_task
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from google.cloud import bigquery
from google.cloud.language import (
    AnalyzeSentimentResponse,
    Document,
    LanguageServiceClient,
)

from ._utils import create_or_replace_intermediate_table, get_parent_updated

# ISO-639-1 Code for English
# all GCP supported languages https://cloud.google.com/natural-language/docs/languages
# we only support EN (had case where sentiment failed by inferring unsupported language)
ENGLISH_ISO_639 = "en"

# over 1000 chars we are charged multiple units of GCP quota
# https://cloud.google.com/natural-language/pricing
CHARS_PER_CREDIT = 1_000
# however there's a limit of 600 requests per minute
# https://cloud.google.com/natural-language/quotas
# so we trade latency (larger batches) to reduce no. of requests
# 10'000 ASCII chars is 10 KB and we found it keeps latency within a few secs
CHARS_LIMIT = CHARS_PER_CREDIT * 10

# every sentence in a batch gets joined into a document from which we recover the scores
# we use a combination of characters that always causes GCP to split text into sentences
DELIMITER = "\n\n"

# round scores since extra precision isn't informative on sentences and displays uglily
SCORES_ROUND_DP = 1

TEXT_COLUMN_NAME = "text"
SENTIMENT_COLUMN_NAME = "sentiment"


class CreditException(Exception):
    def __init__(self, node_id, uses_credits) -> None:
        self.node_id = node_id
        self.uses_credits = uses_credits

    @property
    def node(self):
        return Node.objects.get(pk=self.node_id)


def _remove_unicode(string: str) -> str:
    """Removes non-ASCII characters from string"""
    # https://stackoverflow.com/a/20078869
    return "".join(char for char in string if ord(char) < 128)


def _get_batches_idxs(
    values: List[str], batch_chars: int = CHARS_LIMIT
) -> Tuple[List[List[int]], List[int]]:
    """Helper function to split text data into batches"""
    string_lens = np.array([len(x) for x in values])
    # take into account delimiter which will be added between sentences
    string_lens += len(DELIMITER)

    # each cell of text is assigned to a batch
    batches_idxs = []
    batch_fill = 0
    for i, string_len in enumerate(string_lens):
        if i == 0 or batch_fill + string_len > batch_chars:
            # create a new batch and fill it with this string
            # (allows for text cells exceeding the batch size)
            batches_idxs.append([i])
            batch_fill = string_len
        else:
            # otherwise add strings until the batch is full
            batches_idxs[-1].append(i)
            batch_fill += string_len

    return batches_idxs


def _generate_batches(
    values: List[str], batches_idxs: List[List[int]]
) -> Iterator[List[str]]:
    """Splits a larger list of string text data into batches (<1000 chars by default)"""
    yield from (values[idxs[0] : idxs[-1] + 1] for idxs in batches_idxs)


def _gcp_analyze_sentiment(text: str, client: LanguageServiceClient):
    """Calls GCP sentiment analysis"""
    document = Document(
        content=text,
        type_=Document.Type.PLAIN_TEXT,
        language=ENGLISH_ISO_639,
    )
    return client.analyze_sentiment(document=document)


def _process_batch(values: List[str], client: LanguageServiceClient) -> List[float]:
    """Generates batches of <1MB string text data"""
    text = DELIMITER.join(values)
    # this call is cached in core to avoid hitting GCP and using our quota unnecessarily
    annotations = _gcp_analyze_sentiment(text, client)
    # score/magnitude are like mean/variance respectively
    # magnitude is useful when analysing an entire document
    # here we analyse individual sentences so only care about their scores
    # https://cloud.google.com/natural-language/docs/basics#interpreting_sentiment_analysis_values
    return _reconcile_gcp_scores(values, annotations)


def _reconcile_gcp_scores(
    values: List[str], annotations: AnalyzeSentimentResponse
) -> List[float]:
    """Scores our sentences based on GCP's analysis of the larger text we sent over"""
    scores = []
    i = 0

    for value in values:
        matched = ""
        # can't type-hint sentences as they are a "private" GCP class
        sentences = []  # type: ignore[var-annotated]

        # to each of our sentences might correspond multiple sentences in GCP's analysis
        # so we combine GCP's scores on sub-sentences to score our full sentence
        while matched != value:
            unmatched = value[len(matched) :]

            # handle whitespaces/newlines before next sentence
            if not unmatched.strip():
                matched += unmatched
                continue

            sentence = annotations.sentences[i]
            text = sentence.text.content

            # strip whitespaces/newlines between sentences as GCP discards them
            if not unmatched.lstrip().startswith(text):
                # could happen if our delimiter doesn't cause GCP to split sentences
                # so we end up with a GCP sentence that is a combination of ours
                # and therefore can't be matched to any one of our sentences
                raise ValueError(
                    f"Can't reconcile\n{text}\nwith\n{unmatched}\nfrom\n{value}"
                )

            # handle whitespaces/newlines after previous sentence
            if unmatched != unmatched.lstrip():
                matched += unmatched[: len(unmatched) - len(unmatched.lstrip())]

            matched += text
            sentences.append(sentence)
            i += 1

        # if GCP splits our sentence into multiple sub-sentences we average their scores
        # weighted by their length (i.e. character count) as a simple heuristic
        if all(not s.text.content for s in sentences):
            # special case to avoid division by zero
            score = 0.0
        else:
            score = sum(len(s.text.content) * s.sentiment.score for s in sentences)
            score /= sum(len(s.text.content) for s in sentences)
        score = round(score, SCORES_ROUND_DP)
        scores.append(score)

    return scores


def _compute_values(client, query):

    values = client.query(query).to_dataframe()[TEXT_COLUMN_NAME].to_list()
    values = [_remove_unicode(value) for value in values]

    # clip each row of text so that GPC doesn't charge us more than 1 credit
    # (there are still plenty of characters to infer sentiment for that row)
    clipped_values = [v[:CHARS_PER_CREDIT] for v in values]
    return values, clipped_values


def _update_intermedate_table(ibis_client, node, parent):
    cache_table = node.cache_table
    cache_query = ibis_client.table(
        cache_table.bq_table, database=cache_table.bq_dataset
    )

    # TODO: make sure we don't have column name clash
    query = parent.inner_join(
        cache_query,
        parent[node.sentiment_column] == cache_query[TEXT_COLUMN_NAME],
    ).materialize()[TEXT_COLUMN_NAME, SENTIMENT_COLUMN_NAME]
    return create_or_replace_intermediate_table(
        node,
        query.compile(),
    )


@shared_task
def get_gcp_sentiment(node_id, column_query):

    from apps.nodes.bigquery import get_query_from_node

    node = get_object_or_404(Node, pk=node_id)
    parent = get_query_from_node(node.parents.first())
    conn = clients.ibis_client()
    current_values = parent.relabel(
        {node.sentiment_column: TEXT_COLUMN_NAME}
    ).projection([TEXT_COLUMN_NAME])
    cache_table = node.cache_table

    not_cached = (
        (
            current_values.difference(
                conn.table(
                    cache_table.bq_table, database=cache_table.bq_dataset
                ).projection([TEXT_COLUMN_NAME])
            )
            if cache_table
            else current_values
        )
        .projection([TEXT_COLUMN_NAME])
        .distinct()
    )

    client = clients.bigquery()

    values, clipped_values = _compute_values(client, not_cached.compile())

    if len(values) == 0:
        table = _update_intermedate_table(conn, node, parent)
        return table.bq_table, table.bq_dataset

    if not node.always_use_credits and (
        node.credit_use_confirmed is None
        or node.credit_use_confirmed < max(tuple(get_parent_updated(node)))
    ):
        raise CreditException(node_id, len(values))

    batches_idxs = _get_batches_idxs(clipped_values)
    with ThreadPoolExecutor(max_workers=len(batches_idxs)) as executor:
        batches_scores = executor.map(
            # create one client for all requests so it authenticates only once
            # (GCP auth isn't thread-safe as I saw errors with large no. of requests)
            partial(_process_batch, client=LanguageServiceClient()),
            _generate_batches(clipped_values, batches_idxs),
        )
    scores = [score for batch_scores in batches_scores for score in batch_scores]
    df = pd.DataFrame({TEXT_COLUMN_NAME: values, SENTIMENT_COLUMN_NAME: scores})

    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField(TEXT_COLUMN_NAME, bigquery.enums.SqlTypeNames.STRING),
            bigquery.SchemaField(
                SENTIMENT_COLUMN_NAME, bigquery.enums.SqlTypeNames.FLOAT
            ),
        ],
    )
    with transaction.atomic():
        cache_table, _ = Table.objects.get_or_create(
            source=Table.Source.CACHE_NODE,
            bq_table=node.bq_cache_table_id,
            bq_dataset=node.workflow.project.team.tables_dataset_id,
            project=node.workflow.project,
            cache_node=node,
        )
        job = client.load_table_from_dataframe(
            df, cache_table.bq_id, job_config=job_config
        )  # Make an API request.
        job.result()  # Wait for the job to complete

        node.cache_table = cache_table
        cache_table.data_updated = timezone.now()

        node.workflow.project.team.credittransaction_set.create(
            transaction_type=CreditTransaction.TransactionType.DECREASE,
            amount=len(values),
            user=node.credit_confirmed_user,
        )

        node.save()
        cache_table.save()
        table = _update_intermedate_table(conn, node, parent)
    return table.bq_table, table.bq_dataset
