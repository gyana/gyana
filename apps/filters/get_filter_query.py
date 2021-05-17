from apps.filters.models import Filter


def numeric_filter(query, filter_):
    value = (
        filter_.integer_value
        if filter_.type == Filter.Type.INTEGER
        else filter_.float_value
    )
    if filter_.numeric_predicate == Filter.NumericPredicate.EQUAL:
        return query[query[filter_.column] == value]
    if filter_.numeric_predicate == Filter.NumericPredicate.NEQUAL:
        return query[query[filter_.column] != value]
    if filter_.numeric_predicate == Filter.NumericPredicate.GREATERTHAN:
        return query[query[filter_.column] > value]
    if filter_.numeric_predicate == Filter.NumericPredicate.GREATERTHANEQUAL:
        return query[query[filter_.column] >= value]
    if filter_.numeric_predicate == Filter.NumericPredicate.LESSTHAN:
        return query[query[filter_.column] < value]
    if filter_.numeric_predicate == Filter.NumericPredicate.LESSTHANEQUAL:
        return query[query[filter_.column] <= value]


def create_filter_query(query, filters):
    for filter_ in filters:
        if filter_.type in [Filter.Type.INTEGER, Filter.Type.FLOAT]:
            query = numeric_filter(query, filter_)
        elif filter_.type == Filter.Type.STRING:
            if filter_.string_predicate == Filter.StringPredicate.EQUAL:
                query = query = query[query[filter_.column] == filter_.string_value]
            elif filter_.string_predicate == Filter.StringPredicate.NEQUAL:
                query = query[query[filter_.column] != filter_.string_value]
            elif filter_.string_predicate == Filter.StringPredicate.CONTAINS:
                query = query[query[filter_.column].contains(filter_.string_value)]
            elif filter_.string_predicate == Filter.StringPredicate.NOTCONTAINS:
                query = query[~query[filter_.column].contains(filter_.string_value)]
        elif filter_.type == Filter.Type.BOOL:
            query = query[query[filter_.column] == filter_.bool_value]
    return query
