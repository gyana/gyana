from apps.filters.models import Filter
from rest_framework import serializers

from .models import Node, Workflow


class NodeSerializer(serializers.ModelSerializer):

    workflow = serializers.PrimaryKeyRelatedField(queryset=Workflow.objects.all())
    description = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = (
            "id",
            "kind",
            "name",
            "x",
            "y",
            "workflow",
            "parents",
            "description",
            "error",
            "text_text",
        )

    def get_description(self, obj):
        return DESCRIPTIONS[obj.kind](obj)


def get_limit_desc(obj):
    return f"limit {obj.limit_limit} offset {obj.limit_offset}"


def get_input_desc(obj):
    return f"{obj.input_table.owner_name}" if obj.input_table else ""


def get_output_desc(obj):
    return f"{obj.output_name}"


def get_select_desc(obj):
    return f"Selected {', '.join([col.column for col in obj.columns.all()])}"


def get_join_desc(obj):
    return f"{obj.join_left}={obj.join_right} {obj.join_how}"


def get_aggregation_desc(obj):
    return f"Group by {', '.join([col.column for col in obj.columns.all()])} aggregate {[f'{agg.function}({agg.column}' for agg in obj.aggregations.all()]}"


def get_union_desc(obj):
    return f"Distinct" if obj.union_distinct else ""


def get_sort_desc(obj):
    return f"Sort by {', '.join([s.column + ' '  + ('Ascending' if s.ascending else 'Descending') for s in obj.sort_columns.all()])}"


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
        elif filter_.type == Filter.Type.TIME:
            text = f"{column} is {filter_.time_value}"
        elif filter_.type == Filter.Type.DATETIME:
            text = f"{column} is {filter_.datetime_value}"
        elif filter_.type == Filter.Type.DATE:
            text = f"{column} is {filter_.date_value}"
        filter_descriptions.append(text)

    return f"Filter by {' and '.join(filter_descriptions)}"


def get_edit_desc(obj):
    return f"Edit {' ,'.join([f'{edit.column} {edit.function}' for edit in obj.edit_columns.all()])}"


def get_add_desc(obj):
    return f"Add {' ,'.join([f'{add.column} {add.function}' for add in obj.add_columns.all()])}"


def get_rename_desc(obj):
    texts = [f"{r.column} to {r.new_name}" for r in obj.rename_columns.all()]
    return f"Rename {' ,'.join(texts)}"


def get_text_desc(obj):
    return obj.text_text


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
    "add": get_add_desc,
    "rename": get_rename_desc,
    "text": get_text_desc,
}
