from apps.filters.models import PREDICATE_MAP, Filter


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


def isin(query, column, values):
    return query[query[column].isin(values)]


def notin(query, column, values):
    return query[query[column].notin(values)]


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


FILTER_MAP = {
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
    Filter.NumericPredicate.GREATERTHAN: gt,
    Filter.NumericPredicate.GREATERTHANEQUAL: gte,
    Filter.NumericPredicate.LESSTHAN: lt,
    Filter.NumericPredicate.LESSTHANEQUAL: lte,
    Filter.NumericPredicate.ISIN: isin,
    Filter.NumericPredicate.NOTIN: notin,
}


def create_filter_query(query, filters):
    for filter_ in filters:
        column = filter_.column

        predicate = getattr(filter_, PREDICATE_MAP[filter_.type])
        func = FILTER_MAP[predicate]
        if predicate in ["isin", "notin"]:
            value = getattr(filter_, f"{filter_.type.lower()}_values")
        else:
            value = getattr(filter_, f"{filter_.type.lower()}_value")
        query = func(query, column, value)
    return query
