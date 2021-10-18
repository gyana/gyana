from django.db import models


class AggregationFunctions(models.TextChoices):
    # These functions need to correspond to ibis Column methods
    # https://ibis-project.org/docs/api.html
    SUM = "sum", "Sum"
    COUNT = "count", "Count"
    COUNT_DISTINCT = "nunique", "Count distinct"
    MEAN = "mean", "Average"
    MAX = "max", "Maximum"
    MIN = "min", "Minimum"
    STD = "std", "Standard deviation"


NUMERIC_AGGREGATIONS = list(AggregationFunctions)

DATETIME_AGGREGATIONS = [
    AggregationFunctions.COUNT,
    AggregationFunctions.COUNT_DISTINCT,
    AggregationFunctions.MAX,
    AggregationFunctions.MIN,
]

AGGREGATION_TYPE_MAP = {
    "String": [
        AggregationFunctions.COUNT,
        AggregationFunctions.COUNT_DISTINCT,
    ],
    "Int8": NUMERIC_AGGREGATIONS,
    "Int32": NUMERIC_AGGREGATIONS,
    "Int64": NUMERIC_AGGREGATIONS,
    "Float64": NUMERIC_AGGREGATIONS,
    "Date": DATETIME_AGGREGATIONS,
    "Timestamp": DATETIME_AGGREGATIONS,
    "Time": DATETIME_AGGREGATIONS,
    "Boolean": NUMERIC_AGGREGATIONS,
}
