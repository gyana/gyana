from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Iterator, List, Tuple

import numpy as np
import pandas as pd
from celery.app import shared_task
from django.db import transaction
from django.utils import timezone
from google.cloud import bigquery
from google.cloud.language import (
    AnalyzeSentimentResponse,
    Document,
    LanguageServiceClient,
)

from apps.base import clients
from apps.nodes.exceptions import CreditException
from apps.nodes.models import Node
from apps.tables.models import Table
from apps.teams.models import CreditTransaction, OutOfCreditsException

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
        sentences = []

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
    values = [row[TEXT_COLUMN_NAME] for row in client.query(query).result()]
    cleaned_values = [_remove_unicode(value) for value in values]

    # clip each row of text so that GPC doesn't charge us more than 1 credit
    # (there are still plenty of characters to infer sentiment for that row)
    clipped_values = [v[:CHARS_PER_CREDIT].strip() for v in cleaned_values]
    return values, clipped_values


def _update_intermediate_table(ibis_client, node, current_values):
    cache_table = getattr(node, "cache_table", None)
    cache_query = ibis_client.table(
        cache_table.bq_table, database=cache_table.bq_dataset
    ).relabel({TEXT_COLUMN_NAME: f"{TEXT_COLUMN_NAME}_right"})

    # TODO: make sure we don't have column name clash
    query = current_values.left_join(
        cache_query,
        current_values[TEXT_COLUMN_NAME] == cache_query[f"{TEXT_COLUMN_NAME}_right"],
    )[TEXT_COLUMN_NAME, SENTIMENT_COLUMN_NAME]
    return create_or_replace_intermediate_table(
        node,
        query.compile(),
    )


def _get_current_values(node):
    """Get all current distinct text values and ignore nulls"""
    from apps.nodes.bigquery import get_query_from_node

    parent = get_query_from_node(node.parents.first())
    # We strip whitespace because it interferes with GCPs splitting of sentences
    current_values = (
        parent[[node.sentiment_column]]
        .distinct()
        .relabel({node.sentiment_column: TEXT_COLUMN_NAME})
    )
    return current_values[current_values[TEXT_COLUMN_NAME].notnull()]


def _get_not_cached(node, current_values, ibis_client):
    """Obtain the values that haven't been analysed before"""
    cache_table = getattr(node, "cache_table", None)
    return (
        current_values.difference(
            ibis_client.table(cache_table.bq_table, database=cache_table.bq_dataset)[
                [TEXT_COLUMN_NAME]
            ]
        )
        if cache_table
        else current_values
    )


def _update_cache_table(node, values, scores, bq_client, uses_credits):
    """Upload the newly analysed rows to the cache_table of a node and charge the user"""
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
        # We want to prevent multiple requests triggering updates for the same result
        # Double charging the users
        # TODO: Test whether this really prevents this
        cache_table, _ = Table.objects.select_for_update(nowait=True).get_or_create(
            source=Table.Source.CACHE_NODE,
            bq_table=node.bq_cache_table_id,
            bq_dataset=node.workflow.project.team.tables_dataset_id,
            project=node.workflow.project,
            cache_node=node,
        )
        # Upload to bigquery
        job = bq_client.load_table_from_dataframe(
            df, cache_table.bq_id, job_config=job_config
        )  # Make an API request.
        job.result()  # Wait for the job to complete

        cache_table.data_updated = timezone.now()

        # Charge the user
        node.workflow.project.team.credittransaction_set.create(
            transaction_type=CreditTransaction.TransactionType.INCREASE,
            amount=uses_credits,
            user=node.credit_confirmed_user,
        )

        node.save()
        cache_table.save()


@shared_task(time_limit=60)
def get_gcp_sentiment(node_id):
    """Returns the sentiment from per unique text in a column.

    Results are cached in a bigquery table on a per node basis. When rerunning
    a sentiment analysis only new records are send to the GCP endpoint. Users
    are only charged for these in the end the new and only results are merged
    and the resulting table calculated."""
    node = Node.objects.get(pk=node_id)
    ibis_client = clients.ibis_client()
    bq_client = clients.bigquery()

    current_values = _get_current_values(node)
    not_cached = _get_not_cached(node, current_values, ibis_client)
    values, clipped_values = _compute_values(bq_client, not_cached.compile())

    # If no values to analyse just refetch from cache_table
    uses_credits = len(values)
    if hasattr(node, "cache_table") and uses_credits == 0:

        table = _update_intermediate_table(ibis_client, node, current_values)
        return table.bq_table, table.bq_dataset

    team = node.workflow.project.team
    if team.current_credit_balance + uses_credits > team.credits:
        raise OutOfCreditsException(uses_credits)

    if not node.always_use_credits and (
        node.credit_use_confirmed is None
        or node.credit_use_confirmed < max(tuple(get_parent_updated(node)))
    ):
        raise CreditException(node_id, uses_credits)

    batches_idxs = _get_batches_idxs(clipped_values)
    with ThreadPoolExecutor(max_workers=len(batches_idxs)) as executor:
        batches_scores = executor.map(
            # create one client for all requests so it authenticates only once
            # (GCP auth isn't thread-safe as I saw errors with large no. of requests)
            partial(_process_batch, client=LanguageServiceClient()),
            _generate_batches(clipped_values, batches_idxs),
        )

    scores = [score for batch_scores in batches_scores for score in batch_scores]

    _update_cache_table(node, values, scores, bq_client, uses_credits)
    table = _update_intermediate_table(ibis_client, node, current_values)
    return table.bq_table, table.bq_dataset
