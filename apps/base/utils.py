def create_column_choices(schema):
    columns = sorted([(col, col) for col in schema], key=lambda x: str.casefold(x[1]))
    return [("", "No column selected"), *columns]
