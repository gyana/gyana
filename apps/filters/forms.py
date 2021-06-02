from apps.utils.live_update_form import LiveUpdateForm
from apps.widgets.models import Widget
from django import forms
from django.forms.widgets import HiddenInput, TextInput

from .models import Filter

IBIS_TO_PREDICATE = {"String": "string_predicate", "Int64": "numeric_predicate"}
IBIS_TO_VALUE = {"String": "string_value", "Int64": "integer_value"}
IBIS_TO_TYPE = {"Int64": "INTEGER", "String": "STRING"}


class ColumnChoices:
    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660

        if "columns" in kwargs:
            self.columns = kwargs.pop("columns")
            super().__init__(*args, **kwargs)
            self.fields["column"].choices = self.columns


class FilterForm(LiveUpdateForm):
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

    def get_live_fields(self):

        fields = ["column"]

        column = self.get_live_field("column")
        column_type = None
        if self.schema and column in self.schema:
            column_type = self.schema[column].name

        if column_type == "String":
            fields += ["string_predicate", "string_value"]
        elif column_type == "Int64":
            fields += ["numeric_predicate", "integer_value"]

        return fields

    def __init__(self, *args, **kwargs):

        self.schema = kwargs.pop("schema", None)

        super().__init__(*args, **kwargs)

        if self.schema:
            self.fields["column"].choices = [
                ("", "No column selected"),
            ] + [(col, col) for col in self.schema]

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.column in self.schema:
            instance.type = IBIS_TO_TYPE[self.schema[instance.column].name]

        if commit:
            instance.save()
        return instance


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
