from datetime import datetime

from apps.filters.models import Filter
from apps.integrations.models import Integration
from apps.tables.models import Table
from apps.widgets.models import Widget
from apps.workflows.models import Node, Workflow
from django.conf import settings
from django.db import transaction
from google.cloud import bigquery

from lib.clients import DATAFLOW_ID, DATASET_ID, bigquery_client, ibis_client

DEFAULT_LIMIT = 10


def sync_table(integration: Integration, external_table_id: str):

    client = bigquery_client()

    table_id = f"table_{integration.pk}"

    external_config = create_external_config(integration)
    job_config = bigquery.QueryJobConfig(
        table_definitions={external_table_id: external_config}
    )

    client.query(
        f"CREATE OR REPLACE TABLE {DATASET_ID}.{table_id} AS SELECT * FROM {DATASET_ID}.{external_table_id}",
        job_config=job_config,
    ).result()

    with transaction.atomic():

        if not integration.table_set.exists():
            table = Table(
                source=Table.Source.INTEGRATION,
                bq_table=table_id,
                bq_dataset=DATASET_ID,
                project=integration.project,
                integration=integration,
            )
            table.save()

        integration.last_synced = datetime.now()
        integration.save()


def create_external_config(integration: Integration):
    if integration.kind == Integration.Kind.GOOGLE_SHEETS:
        # https://cloud.google.com/bigquery/external-data-drive#python
        external_config = bigquery.ExternalConfig("GOOGLE_SHEETS")
        external_config.source_uris = [integration.url]
    elif integration.kind == Integration.Kind.CSV:
        external_config = bigquery.ExternalConfig("CSV")
        external_config.source_uris = [
            f"gs://{settings.GS_BUCKET_NAME}/{integration.file.name}"
        ]

    external_config.autodetect = True

    return external_config


def create_external_table(integration: Integration) -> str:

    client = bigquery_client()
    external_table_id = f"table_{integration.pk}_external"

    bq_dataset = client.get_dataset(DATASET_ID)

    external_table = bigquery.Table(bq_dataset.table(external_table_id))

    external_config = create_external_config(integration)

    external_table.external_data_configuration = external_config
    external_table = client.create_table(external_table, exists_ok=True)

    return external_table_id


def query_integration(integration: Integration):

    if not integration.table_set.exists():
        external_table_id = create_external_table(integration)
        sync_table(integration, external_table_id)

    conn = ibis_client()
    table = conn.table(integration.table_set.first().bq_table)

    return conn.execute(table.limit(DEFAULT_LIMIT))


def run_workflow(workflow: Workflow):
    output_nodes = workflow.node_set.filter(kind=Node.Kind.OUTPUT).all()

    for node in output_nodes:
        client = bigquery_client()
        query = node.get_query().compile()

        try:
            client.query(
                f"CREATE OR REPLACE TABLE {DATAFLOW_ID}.{node.table.bq_table} as ({query})"
            ).result()

        except Table.DoesNotExist:
            table_id = f"table_{node.pk}"
            client.query(
                f"CREATE OR REPLACE TABLE {DATAFLOW_ID}.{table_id} as ({query})"
            ).result()

            table = Table(
                source=Table.Source.WORKFLOW_NODE,
                bq_table=table_id,
                bq_dataset=DATAFLOW_ID,
                project=workflow.project,
                workflow_node=node,
            )
            table.save()

    workflow.last_run = datetime.now()


def query_widget(widget: Widget):

    conn = ibis_client()

    table = widget.table.get_query()

    for filter in widget.filter_set.all():
        if filter.type == Filter.Type.INTEGER:
            if filter.integer_predicate == Filter.IntegerPredicate.EQUAL:
                table = table[table[filter.column] == filter.integer_value]
            elif filter.integer_predicate == Filter.IntegerPredicate.EQUAL:
                table = table[table[filter.column] != filter.integer_value]
        elif filter.type == Filter.Type.STRING:
            if filter.string_predicate == Filter.StringPredicate.STARTSWITH:
                table = table[table[filter.column].str.startswith(filter.string_value)]
            elif filter.string_predicate == Filter.StringPredicate.ENDSWITH:
                table = table[table[filter.column].str.endswith(filter.string_value)]

    return conn.execute(table.group_by(widget.label).count(widget.value))
