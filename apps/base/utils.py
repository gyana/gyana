def create_column_choices(schema):
    return [("", "No column selected"), *[(col, col) for col in schema]]
