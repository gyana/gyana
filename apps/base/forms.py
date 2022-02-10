from functools import cache

from django import forms
from django.db import transaction
from django.utils.datastructures import MultiValueDict

from apps.base.core.utils import create_column_choices

# temporary overrides for formset labels
FORMSET_LABELS = {
    "columns": "Group columns",
    "aggregations": "Aggregations",
    "sort_columns": "Sort columns",
    "edit_columns": "Edit columns",
    "add_columns": "Add columns",
    "rename_columns": "Rename columns",
    "formula_columns": "Formula columns",
    "join_columns": "Joins",
    "filters": "Filters",
    "secondary_columns": "Select specific columns",
    "window_columns": "Window columns",
    "convert_columns": "Select columns to convert",
    "values": "Additional values",
    "charts": "Charts",
    "queryparams": "Query Params",
    "httpheaders": "HTTP Headers",
    "formdataentries": "Form Data",
    "formurlencodedentries": "Form Data",
}


def _get_formset_label(formset):
    prefix = formset.get_default_prefix()
    return FORMSET_LABELS.get(prefix, prefix)


class SchemaFormMixin:
    @property
    def column_type(self):
        column = self.get_live_field("column")
        if self.schema and column in self.schema:
            return self.schema[column]
        return None

    def __init__(self, *args, **kwargs):
        self.schema = kwargs.pop("schema", None)

        super().__init__(*args, **kwargs)

        if self.fields.get("column"):
            self.fields["column"] = forms.ChoiceField(
                choices=create_column_choices(self.schema),
                help_text=self.base_fields["column"].help_text,
            )


class BaseModelForm(forms.ModelForm):
    def pre_save(self, instance):
        # override in child to add behaviour on commit save
        pass

    def post_save(self, instance):
        # override in child to add behaviour on commit save
        pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit == True:
            with transaction.atomic():
                self.pre_save(instance)
                instance.save()
                self.save_m2m()
                self.post_save(instance)
        return instance


class LiveUpdateForm(BaseModelForm):

    hidden_live = forms.CharField(widget=forms.HiddenInput(), required=True)

    def _update_data_with_initial(self):
        """Updates the form's data missing fields with the initial values.

        Because LiveForms don't hold data for fields that haven't been displayed,
        we need to manually add these values."""
        # When submitting we don't need to do anything
        if not self.is_live:
            return
        # self.data hold data from request.POST and can be a MultiValueDict or a QueryDict
        data = MultiValueDict({**self.data})
        for field in self.get_live_fields():
            # self.initial is a dict holding the model data that
            # For the additional formset rows that added as placeholders
            # self.initial is empty.
            if field not in self.data and self.initial.get(field) is not None:
                initial = self.initial[field]
                # e.g. for an ArrayField, each item should be a separate value (rather than one value as a list)
                if isinstance(initial, list):
                    data.setlist(field, initial)
                else:
                    data[field] = initial
            # HTML forms usually just omit unchecked checkboxes
            # For us this is undistinguishable from the field not having been shown before
            # In the LiveFormController we manually add these fields to the form data
            # Just to remove them here again
            elif (
                isinstance(self.fields[field], forms.BooleanField)
                and self.data.get(field) == "false"
            ):
                data.pop(field)

        self.data = data

    def __init__(self, *args, **kwargs):

        self.parent_instance = kwargs.pop("parent_instance", None)

        super().__init__(*args, **kwargs)

        self.prefix = kwargs.pop("prefix", None)

        # the rendered fields are determined by the values of the other fields
        live_fields = self.get_live_fields()
        self._update_data_with_initial()
        # - when the Stimulus controller makes a POST request, it will always be invalid
        # and re-render the same form with the updated values
        # - when the form is valid and the user clicks a submit button, the live field is
        # not rendered and it behaves like a normal form
        if self.is_live:
            live_fields += ["hidden_live"]
        self.fields = {k: v for k, v in self.fields.items() if k in live_fields}

    @property
    def is_live(self):
        # the "submit" value is populated when the user clicks the button
        return "submit" not in self.data

    def get_live_field(self, name):
        # potentially called before self._update_data_with_initial
        # formset data is prefixed
        key_ = f"{self.prefix}-{name}" if self.prefix else name

        # data populated by POST request in update
        # as a fallback we are using the database value

        return self.data.get(key_) or getattr(self.instance, name)

    def get_live_fields(self):
        # by default the behaviour is a normal form
        return [f for f in self.fields.keys() if f != "hidden_live"]

    @property
    def deleted(self):
        return self.data.get(f"{self.prefix}-DELETE") == "on"


class BaseLiveSchemaForm(SchemaFormMixin, LiveUpdateForm):
    pass


class BaseSchemaForm(SchemaFormMixin, forms.ModelForm):
    pass


class LiveFormsetMixin:
    def get_live_formsets(self):
        return []

    def get_formset_kwargs(self, formset):
        return {}

    def get_formset_form_kwargs(self, formset):
        return {}

    def get_formset(self, formset):
        forms_kwargs = self.get_formset_form_kwargs(formset)

        # provide a reference to parent instance in live update forms
        if issubclass(formset.form, LiveUpdateForm):
            forms_kwargs["parent_instance"] = self.instance

        if issubclass(formset.form, SchemaFormMixin):
            forms_kwargs["schema"] = self.schema

        formset = (
            # POST request for form creation
            formset(
                self.data,
                # self.request.FILES,?
                instance=self.instance,
                **self.get_formset_kwargs(formset),
                form_kwargs=forms_kwargs,
            )
            # form is only bound if formset is in previous render, otherwise load from database
            if self.data and f"{formset.get_default_prefix()}-TOTAL_FORMS" in self.data
            # initial render
            else formset(
                instance=self.instance,
                **self.get_formset_kwargs(formset),
                form_kwargs=forms_kwargs,
            )
        )
        # When the post contains the wrong total forms number new forms aren't
        # created. This happens for example when changing the widget kind.
        if len(formset.forms) < formset.min_num:
            formset.forms.extend(
                formset._construct_form(i, **forms_kwargs)
                for i in range(len(formset.forms), formset.min_num)
            )

        return formset

    @cache
    def get_formsets(self):
        return {
            _get_formset_label(formset): self.get_formset(formset)
            for formset in self.get_live_formsets()
        }


class LiveFormsetForm(LiveFormsetMixin, BaseLiveSchemaForm):
    pass
