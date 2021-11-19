def slice_query(query, column, date_slicer):
    if date_slicer.start:
        query = query[query[column] > date_slicer.start]

    if date_slicer.end:
        query = query[query[column] < date_slicer.end]

    return query
