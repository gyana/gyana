from itertools import count, filterfalse

from django.db import transaction
from rest_framework import serializers

from apps.filters.models import Filter

from .config import NODE_CONFIG
from .models import Node, NodeParents, Workflow


# Serialize model with a m2m through model inspired by
# https://stackoverflow.com/questions/17256724/include-intermediary-through-model-in-responses-in-django-rest-framework
class ParentshipSerializer(serializers.HyperlinkedModelSerializer):
    parent_id = serializers.ReadOnlyField(source="parent.id")

    class Meta:
        model = NodeParents
        fields = ("id", "parent_id", "position")


class NodeSerializer(serializers.ModelSerializer):

    workflow = serializers.PrimaryKeyRelatedField(queryset=Workflow.objects.all())
    description = serializers.SerializerMethodField()
    parents = ParentshipSerializer(source="parent_set", many=True, required=False)

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
            "parents",
        )

    def create(self, validated_data):
        # Parents are only provided in tests right now
        parent_set = validated_data.pop("parent_set", None)
        instance = super().create(validated_data)
        if parent_set:
            self.update_parents(instance)
        return instance

    def update_parents(self, instance):
        # The frontend sends a list of all parents so we need to figure out
        # which ones to delete and which ones to add
        current_parents = instance.parent_set.all()
        new_parents = self.initial_data["parents"]
        to_be_deleted = [
            parent
            for parent in current_parents
            if parent.parent_id
            not in [int(parent["parent_id"]) for parent in new_parents]
        ]
        to_be_created = [
            parent["parent_id"]
            for parent in new_parents
            if int(parent["parent_id"])
            not in [parent.parent_id for parent in current_parents]
        ]
        existing_positions = [
            parent.position for parent in current_parents if parent not in to_be_deleted
        ]
        with transaction.atomic():

            for parent in to_be_deleted:
                parent.delete()

            # We want to make sure parents are always added incrementally so
            # We always fill the missing positions starting from 0
            for parent in to_be_created:
                position = next(filterfalse(existing_positions.__contains__, count(0)))
                instance.parent_set.create(parent_id=parent, position=position)

                existing_positions.append(position)

    def update(self, instance, validated_data):
        if "parent_set" in validated_data:
            self.update_parents(instance)
            validated_data.pop("parent_set")

        return super().update(instance, validated_data)

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
    return f"{obj.join_left}={obj.join_right} {obj.join_how}"


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
}
