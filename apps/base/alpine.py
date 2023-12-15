from apps.base.core.aggregations import AGGREGATION_TYPE_MAP
from apps.columns.bigquery import AllOperations, DatePeriod
from apps.columns.forms import IBIS_TO_FUNCTION

aggregations = {k: [x.value for x in v] for k, v in AGGREGATION_TYPE_MAP.items()}
date_periods = {
    "Date": [DatePeriod.DATE.value],
    "Timestamp": [x.value for x in DatePeriod],
}
operations = {
    f: [k for k, v in AllOperations.items() if v.arguments == 1 and v.value_field == f]
    for f in (
        "integer_value",
        "float_value",
        "string_value",
    )
}

ibis_store = {
    "aggregations": aggregations,
    "functions": IBIS_TO_FUNCTION,
    "date_periods": date_periods,
    "operations": operations,
}
