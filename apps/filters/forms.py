from apps.utils.live_update_form import LiveUpdateForm
from apps.utils.schema_form_mixin import SchemaFormMixin
from dal import autocomplete
from django import forms
from django.forms.widgets import TextInput

IBIS_TO_TYPE = {"Int64": "INTEGER", "String": "STRING"}


def get_choice_list():
    return [
        ["France_value", "France"],
        ["Fiji_value", "Fiji"],
        ["Finland_value", "Finland"],
        ["Switzerland_value", "Switzerland"],
    ]


class FilterForm(SchemaFormMixin, LiveUpdateForm):
    column = forms.ChoiceField(choices=[])
    string_values = autocomplete.Select2ListChoiceField(
        choice_list=get_choice_list,
        widget=autocomplete.ListSelect2(url="workflows:array_autocomplete"),
    )
    integer_values = autocomplete.Select2ListChoiceField(
        choice_list=get_choice_list,
        widget=autocomplete.ListSelect2(url="workflows:array_autocomplete"),
    )
    float_values = autocomplete.Select2ListChoiceField(
        choice_list=get_choice_list,
        widget=autocomplete.ListSelect2(url="workflows:array_autocomplete"),
    )

    class Meta:
        fields = (
            "column",
            "string_predicate",
            "numeric_predicate",
            "string_value",
            "integer_value",
            "string_values",
            "integer_values",
        )
        widgets = {
            "string_value": TextInput(),
        }

    def get_live_fields(self):

        fields = ["column"]
        predicate = None
        if self.column_type == "String":
            predicate = "string_predicate"
            value = "string_value"
            fields += [predicate]
        elif self.column_type == "Int64":
            predicate = "numeric_predicate"
            value = "integer_value"
            fields += ["numeric_predicate"]

        if (
            self.column_type
            and predicate
            and (pred := self.get_live_field(predicate)) is not None
            and pred
            not in [
                "isnull",
                "notnull",
            ]
        ):
            if pred in ["isin", "notin"]:
                fields += [value + "s"]
            else:
                fields += [value]

        return fields

    def __init__(self, *args, **kwargs):

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
