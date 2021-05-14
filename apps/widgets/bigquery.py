from apps.filters.models import Filter
from apps.widgets.models import Widget
from lib.clients import ibis_client


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
