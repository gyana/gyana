from apps.filters.models import Filter


def eq(query, column, value):
    return query[query[column] == value]


def neq(query, column, value):
    return query[query[column] != value]


def gt(query, column, value):
    return query[query[column] > value]


def gte(query, column, value):
    return query[query[column] >= value]


def lt(query, column, value):
    return query[query[column] < value]


def lte(query, column, value):
    return query[query[column] <= value]


def isnull(query, column, value):
    return query[query[column].isnull()]


def notnull(query, column, value):
    return query[query[column].notnull()]


NUMERIC_FILTER = {
    Filter.NumericPredicate.EQUAL: eq,
    Filter.NumericPredicate.NEQUAL: neq,
    Filter.NumericPredicate.GREATERTHAN: gt,
    Filter.NumericPredicate.GREATERTHANEQUAL: gte,
    Filter.NumericPredicate.LESSTHAN: lt,
    Filter.NumericPredicate.LESSTHANEQUAL: lte,
    Filter.NumericPredicate.ISNULL: isnull,
    Filter.NumericPredicate.NOTNULL: notnull,
}


def isin(query, column, values):
    return query[query[column].isin(values)]


def notin(query, column, values):
    return query[query[column].notin(values)]


ARRAY_FILTER = {
    Filter.NumericPredicate.ISIN: isin,
    Filter.NumericPredicate.NOTIN: notin,
}


def numeric_filter(query, filter_):
    value = (
        filter_.integer_value
        if filter_.type == Filter.Type.INTEGER
        else filter_.float_value
    )
    column = filter_.column
    func = NUMERIC_FILTER.get(filter_.numeric_predicate)
    if func:
        return func(query, column, value)
    values = (
        filter_.integer_values
        if filter_.type == Filter.Type.INTEGER
        else filter_.float_values
    )
    func = ARRAY_FILTER[filter_.numeric_predicate]
    return func(query, column, values)


def contains(query, column, value):
    return query[query[column].contains(value)]


def not_contains(query, column, value):
    return query[~query[column].contains(value)]


def startswith(query, column, value):
    return query[query[column].startswith(value)]


def endswith(query, column, value):
    return query[query[column].endswith(value)]


def islower(query, column, value):
    return query[query[column] == query[column].lower()]


def isupper(query, column, value):
    return query[query[column] == query[column].upper()]


STRING_FILTER = {
    Filter.StringPredicate.EQUAL: eq,
    Filter.StringPredicate.NEQUAL: neq,
    Filter.StringPredicate.CONTAINS: contains,
    Filter.StringPredicate.NOTCONTAINS: not_contains,
    Filter.StringPredicate.ISNULL: isnull,
    Filter.StringPredicate.NOTNULL: notnull,
    Filter.StringPredicate.STARTSWITH: startswith,
    Filter.StringPredicate.ENDSWITH: endswith,
    Filter.StringPredicate.ISUPPERCASE: isupper,
    Filter.StringPredicate.ISLOWERCASE: islower,
}


def string_filter(query, filter_):
    value = filter_.string_value
    column = filter_.column
    func = STRING_FILTER.get(filter_.string_predicate)
    if func:
        return func(query, column, value)
    values = filter_.string_values
    func = ARRAY_FILTER[filter_.string_predicate]
    return func(query, column, values)


def create_filter_query(query, filters):
    for filter_ in filters:
        column = filter_.column
        if filter_.type in [Filter.Type.INTEGER, Filter.Type.FLOAT]:
            query = numeric_filter(query, filter_)
        elif filter_.type == Filter.Type.STRING:
            query = string_filter(query, filter_)
        elif filter_.type == Filter.Type.BOOL:
            query = query[query[column] == filter_.bool_value]
    return query
