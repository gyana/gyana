from datetime import datetime

from apps.filters.models import Filter
from apps.tables.models import Table
from apps.widgets.models import Widget
from apps.workflows.models import Node, Workflow

from lib.clients import DATAFLOW_ID, bigquery_client, ibis_client

DEFAULT_LIMIT = 10


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

    if widget.aggregator == Widget.Aggregator.NONE:
        return conn.execute(table.projection([widget.label, widget.value]))
    else:
        return conn.execute(
            table.group_by(widget.label).aggregate(
                getattr(table[widget.value], widget.aggregator)().name(widget.value)
            )
        )
