from rest_framework import serializers

from apps.filters.models import Filter
from apps.tables.models import Table

from .config import NODE_CONFIG
from .models import Edge, Node, Workflow


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ("id", "owner_name")


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = ("id", "child", "parent", "position")


class NodeSerializer(serializers.ModelSerializer):

    workflow = serializers.PrimaryKeyRelatedField(queryset=Workflow.objects.all())
    description = serializers.SerializerMethodField()
    input_table = TableSerializer(many=False, required=False)
    parent_edges = EdgeSerializer(many=True, required=False)

    class Meta:
        model = Node
        fields = (
            "id",
            "kind",
            "name",
            "x",
            "y",
            "workflow",
            "input_table",
            "description",
            "error",
            "text_text",
            "parent_edges",
            "join_is_valid",
        )
        read_only = ["parent_edges"]

    def get_description(self, obj):
        return DESCRIPTIONS[obj.kind](obj)


def get_limit_desc(obj):
    return f"limit {obj.limit_limit} offset {obj.limit_offset}"


def get_input_desc(obj):
    return f"{obj.input_table.owner_name if obj.input_table else 'No input'} selected"


def get_output_desc(obj):
    return f"{obj.name or 'No name'} selected"


def get_select_desc(obj):
    return f"Selected {', '.join([col.column for col in obj.columns.all()])}"


def get_join_desc(obj):
    return f"Join {', '.join([f'Input {i+2} on {column.left_column}={column.right_column}' for i, column in enumerate(obj.join_columns.all())])}"


def get_aggregation_desc(obj):
    return f"Group by {', '.join([col.column for col in obj.columns.all()])} aggregate {[f'{agg.function}({agg.column}' for agg in obj.aggregations.all()]}"


def get_union_desc(obj):
    return "Distinct" if obj.union_distinct else ""


def get_except_desc(obj):
    return "Except"


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
            text = f"{column} {filter_.bool_predicate}"
        elif filter_.type == Filter.Type.TIME:
            text = f"{column} is {filter_.time_value}"
        elif filter_.type == Filter.Type.DATETIME:
            text = f"{column} is {filter_.datetime_value}"
        elif filter_.type == Filter.Type.DATE:
            text = f"{column} is {filter_.date_value}"
        elif filter_.type == Filter.Type.STRUCT:
            text = f"{column} {filter_.struct_predicate}"
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


def get_formula_desc(obj):
    return f"Add {' ,'.join([f'{formula.formula} as {formula.label}' for formula in obj.formula_columns.all()])}"


def get_distinct_desc(obj):
    return f"Distinct on {', '.join([col.column for col in obj.columns.all()])}"


def get_pivot_desc(obj):
    return (
        f"Pivoting {obj.pivot_column} with {obj.pivot_aggregation}({obj.pivot_value})"
        f"{'over '+ obj.pivot_index if obj.pivot_index else ''}"
    )


def get_unpivot_desc(obj):
    return f"Unpivoting {' ,'.join([col.column for col in obj.columns.all()])} to {obj.unpivot_value})"


def get_intersection_desc(obj):
    return f"Intersection between {' ,'.join((parent.name or NODE_CONFIG[parent.kind]['displayName'] for parent in obj.parents.all()))}"


def get_window_desc(obj):
    texts = [
        f'{window.label}: {window.function}({window.column}) OVER({"PARTION BY " + window.group_by if window.group_by else ""} {"ORDER BY " + window.order_by if window.order_by else ""})'
        for window in obj.window_columns.all()
    ]
    return f"Add window columns: {', '.join(texts)}"


def get_sentiment_desc(obj):
    return f"Analysis sentiment of {obj.sentiment_column}."


def get_convert_desc(obj):
    return f"Convert {', '.join(f'{col.column} to {col.target_type}' for col in obj.convert_columns.iterator())}"


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
    "except": get_except_desc,
    "rename": get_rename_desc,
    "text": get_text_desc,
    "formula": get_formula_desc,
    "distinct": get_distinct_desc,
    "pivot": get_pivot_desc,
    "unpivot": get_unpivot_desc,
    "intersect": get_intersection_desc,
    "sentiment": get_sentiment_desc,
    "window": get_window_desc,
    "convert": get_convert_desc,
}
