from apps.filters.models import Filter
from rest_framework import serializers

from .models import Node, Workflow


class NodeSerializer(serializers.ModelSerializer):

    workflow = serializers.PrimaryKeyRelatedField(queryset=Workflow.objects.all())
    description = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = ("id", "kind", "x", "y", "workflow", "parents", "description", "error")

    def get_description(self, obj):
        return DESCRIPTIONS[obj.kind](obj)


def get_limit_desc(obj):
    return f"limit {obj.limit_limit} offset {obj.limit_offset}"


def get_input_desc(obj):
    return f"{obj.input_table.owner_name}" if obj.input_table else ""


def get_output_desc(obj):
    return f"{obj.output_name}"


def get_select_desc(obj):
    return f"Selected {', '.join([col.name for col in obj.columns.all()])}"


def get_join_desc(obj):
    return f"{obj.join_left}={obj.join_right} {obj.join_how}"


def get_aggregation_desc(obj):
    return f"Group by {', '.join([col.name for col in obj.columns.all()])} aggregate {[f'{agg.function}({agg.name}' for agg in obj.aggregations.all()]}"


def get_union_desc(obj):
    return f"Distinct" if obj.union_distinct else ""


def get_sort_desc(obj):
    return f"Sort by {', '.join([s.name + ' '  + ('Ascending' if s.ascending else 'Descending') for s in obj.sort_columns.all()])}"


def get_filter_desc(obj):
    filter_descriptions = []

    for filter_ in obj.filters.all():
        column = filter_.column
        if filter_.type == Filter.Type.INTEGER:
            text = f"{column} {filter_.numeric_predicate} {filter_.integer_value}"
        elif filter_.type == Filter.Type.FLOAT:
            text = f"{column} {filter_.numeric_predicate} {filter_.float_value}"
        elif filter_.type == Filter.Type.STRING:
            text = f"{column} {filter_.string_predicate} {filter_.string_value}"
        elif filter_.type == Filter.Type.BOOL:
            text = f"{column} is {filter_.bool_value}"
        filter_descriptions.append(text)

    return f"Filter by {' and '.join(filter_descriptions)}"


def get_edit_desc(obj):
    return f"Edit {' ,'.join([f'{edit.name} {edit.function}' for edit in obj.edit_columns.all()])}"


DESCRIPTIONS = {
    "input": get_input_desc,
    "limit": get_limit_desc,
    "output": get_output_desc,
    "select": get_select_desc,
    "join": get_join_desc,
    "aggregation": get_aggregation_desc,
    "union": get_union_desc,
    "sort": get_sort_desc,
    "filter": get_filter_desc,
    "edit": get_edit_desc,
}
