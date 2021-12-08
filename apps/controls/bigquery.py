from apps.filters.bigquery import DATETIME_FILTERS

from .models import CustomChoice


def slice_query(query, column, control):
    if control.date_range != CustomChoice.CUSTOM:
        range_filter = DATETIME_FILTERS[control.date_range]
        return range_filter(query, column)

    if control.start:
        query = query[query[column] > control.start]

    if control.end:
        query = query[query[column] < control.end]

    return query
