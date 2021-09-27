from django import forms


class SchemaFormMixin:
    @property
    def column_type(self):
        column = self.get_live_field("column")
        if self.schema and column in self.schema:
            return self.schema[column].name
        return None

    def __init__(self, *args, **kwargs):
        self.schema = kwargs.pop("schema", None)

        super().__init__(*args, **kwargs)

        if self.fields.get("column"):
            self.fields["column"] = forms.ChoiceField(
                choices=[
                    ("", "No column selected"),
                    *[(col, col) for col in self.schema],
                ],
                help_text=self.base_fields["column"].help_text,
            )
