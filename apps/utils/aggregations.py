from django.db import models


class AggregationFunctions(models.TextChoices):
    # These functions need to correspond to ibis Column methods
    # https://ibis-project.org/docs/api.html
    SUM = "sum", "Sum"
    COUNT = "count", "Count"
    MEAN = "mean", "Average"
    MAX = "max", "Maximum"
    MIN = "min", "Minimum"
    STD = "std", "Standard deviation"


NUMERIC_AGGREGATIONS = list(AggregationFunctions)

AGGREGATION_TYPE_MAP = {
    "String": [AggregationFunctions.COUNT],
    "Int64": NUMERIC_AGGREGATIONS,
    "Float64": NUMERIC_AGGREGATIONS,
}
