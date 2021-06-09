from apps.filters.models import Filter


def numeric_filter(query, filter_):
    value = (
        filter_.integer_value
        if filter_.type == Filter.Type.INTEGER
        else filter_.float_value
    )
    column = filter_.column
    if filter_.numeric_predicate == Filter.NumericPredicate.EQUAL:
        return query[query[column] == value]
    if filter_.numeric_predicate == Filter.NumericPredicate.NEQUAL:
        return query[query[column] != value]
    if filter_.numeric_predicate == Filter.NumericPredicate.GREATERTHAN:
        return query[query[column] > value]
    if filter_.numeric_predicate == Filter.NumericPredicate.GREATERTHANEQUAL:
        return query[query[column] >= value]
    if filter_.numeric_predicate == Filter.NumericPredicate.LESSTHAN:
        return query[query[column] < value]
    if filter_.numeric_predicate == Filter.NumericPredicate.LESSTHANEQUAL:
        return query[query[column] <= value]
    if filter_.numeric_predicate == Filter.NumericPredicate.ISNULL:
        return query[query[column].isnull()]
    if filter_.numeric_predicate == Filter.NumericPredicate.NOTNULL:
        return query[query[column].notnull()]

    values = (
        filter_.integer_values
        if filter_.type == Filter.Type.INTEGER
        else filter_.float_values
    )
    if filter_.numeric_predicate == Filter.NumericPredicate.ISIN:
        return query[query[column].isin(values)]

    if filter_.numeric_predicate == Filter.NumericPredicate.NOTIN:
        return query[query[column].notin(values)]


def create_filter_query(query, filters):
    for filter_ in filters:
        column = filter_.column
        if filter_.type in [Filter.Type.INTEGER, Filter.Type.FLOAT]:
            query = numeric_filter(query, filter_)
        elif filter_.type == Filter.Type.STRING:
            if filter_.string_predicate == Filter.StringPredicate.EQUAL:
                query = query[query[column] == filter_.string_value]
            elif filter_.string_predicate == Filter.StringPredicate.NEQUAL:
                query = query[query[column] != filter_.string_value]
            elif filter_.string_predicate == Filter.StringPredicate.CONTAINS:
                query = query[query[column].contains(filter_.string_value)]
            elif filter_.string_predicate == Filter.StringPredicate.NOTCONTAINS:
                query = query[~query[column].contains(filter_.string_value)]
            elif filter_.string_predicate == Filter.StringPredicate.STARTSWITH:
                query = query[query[column].startswith(filter_.string_value)]
            elif filter_.string_predicate == Filter.StringPredicate.ENDSWITH:
                query = query[query[column].endswith(filter_.string_value)]
            elif filter_.string_predicate == Filter.StringPredicate.ISNULL:
                query = query[query[column].isnull()]
            elif filter_.string_predicate == Filter.StringPredicate.NOTNULL:
                query = query[query[column].notnull()]
            elif filter_.string_predicate == Filter.StringPredicate.ISUPPERCASE:
                query = query[query[column] == query[column].upper()]
            elif filter_.string_predicate == Filter.StringPredicate.ISLOWERCASE:
                query = query[query[column] == query[column].lower()]
            elif filter_.string_predicate == Filter.StringPredicate.ISIN:
                query = query[query[column].isin(filter_.string_values)]
            elif filter_.string_predicate == Filter.StringPredicate.NOTIN:
                query = query[query[column].notin(filter_.string_values)]
        elif filter_.type == Filter.Type.BOOL:
            query = query[query[column] == filter_.bool_value]
    return query
