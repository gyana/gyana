class SchemaFormMixin:
    @property
    def column_type(self):
        column = self.get_live_field("column")
        if column in self.schema:
            return self.schema[column].name
        return None

    def __init__(self, *args, **kwargs):
        self.schema = kwargs.pop("schema")

        super().__init__(*args, **kwargs)
