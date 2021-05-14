from apps.filters.models import Filter


def create_filter_query(query, filters):
    for filter_ in filters:
        if filter_.type == Filter.Type.INTEGER:
            if filter_.integer_predicate == Filter.IntegerPredicate.EQUAL:
                query = query[query[filter_.column] == filter_.integer_value]
        elif filter_.type == Filter.Type.STRING:
            if filter_.string_predicate == Filter.StringPredicate.STARTSWITH:
                query = query[
                    query[filter_.column].str.startswith(filter_.string_value)
                ]
            elif filter_.string_predicate == Filter.StringPredicate.ENDSWITH:
                query = query[query[filter_.column].str.endswith(filter_.string_value)]
    return query
