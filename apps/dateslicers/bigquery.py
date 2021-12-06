from apps.filters.bigquery import DATETIME_FILTERS

from .models import CustomChoice


def slice_query(query, column, date_slicer):
    if date_slicer.date_range != CustomChoice.CUSTOM:
        range_filter = DATETIME_FILTERS[date_slicer.date_range]
        return range_filter(query, column)

    if date_slicer.start:
        query = query[query[column] > date_slicer.start]

    if date_slicer.end:
        query = query[query[column] < date_slicer.end]

    return query
