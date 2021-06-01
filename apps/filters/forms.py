from apps.widgets.models import Widget
from django import forms
from django.forms.widgets import HiddenInput, TextInput

from .models import Filter

IBIS_TO_PREDICATE = {"String": "string_predicate", "Int64": "numeric_predicate"}
IBIS_TO_VALUE = {"String": "string_value", "Int64": "integer_value"}


class ColumnChoices:
    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660

        if "columns" in kwargs:
            self.columns = kwargs.pop("columns")
            super().__init__(*args, **kwargs)
            self.fields["column"].choices = self.columns


class FilterForm(forms.ModelForm):
    column = forms.ChoiceField(choices=[])

    class Meta:
        fields = (
            "column",
            "string_predicate",
            "numeric_predicate",
            "string_value",
            "integer_value",
        )
        widgets = {"string_value": TextInput()}

    def get_live_field(self, name):

        # data populated by POST request in update
        if name in self.data:
            return self.data[name]

        # data populated by GET request in live form
        if name in self.initial:
            return self.initial[name]

        # data populated from database in initial render
        return getattr(self.instance, name, None)

    def get_live_fields(self):

        fields = ["column"]

        column = self.get_live_field("column")
        column_type = None
        if column in self.schema:
            column_type = self.schema[column].name

        if column_type == "String":
            fields += ["string_predicate", "string_value"]
        elif column_type == "Int64":
            fields += ["numeric_predicate", "integer_value"]

        return fields

    def __init__(self, *args, **kwargs):

        project = kwargs.pop("project", None)
        self.schema = kwargs.pop("schema")

        super().__init__(*args, **kwargs)

        self.fields["column"].choices = [(col, col) for col in self.schema]

        keep_fields = self.get_live_fields()

        self.fields = {k: v for k, v in self.fields.items() if k in keep_fields}


def get_filter_form(parent_fk, column_type=None):

    fields = ["column", parent_fk]
    if column_type is not None:
        fields += [IBIS_TO_PREDICATE[column_type.name], IBIS_TO_VALUE[column_type.name]]

    meta = type(
        "Meta",
        (),
        {"model": Filter, "fields": fields, "widgets": {parent_fk: HiddenInput()}},
    )

    return type(
        "FilterForm",
        (
            ColumnChoices,
            forms.ModelForm,
        ),
        {"Meta": meta, "column": forms.ChoiceField(choices=())},
    )
