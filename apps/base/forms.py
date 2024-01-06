import json
from functools import cache

from crispy_forms import utils
from crispy_forms.helper import FormHelper
from django import forms
from django.contrib.postgres.search import TrigramSimilarity
from django.db import transaction
from django.db.models import Case, Q, When
from django.db.models.functions import Greatest
from django.forms.models import ModelFormOptions
from django.utils.datastructures import MultiValueDict

from apps.base.core.utils import create_column_choices
from apps.tables.models import Table


# By default, django-crispy-form caches the template, breaking hot-reloading in development
def default_field_template(template_pack=utils.TEMPLATE_PACK):
    return utils.get_template("%s/field.html" % template_pack)


utils.default_field_template = default_field_template

ModelFormOptions__init__ = ModelFormOptions.__init__


def __init__(self, options=None):
    ModelFormOptions__init__(self, options=options)
    self.show = getattr(options, "show", None)
    self.effect = getattr(options, "effect", {})


ModelFormOptions.__init__ = __init__


def get_formsets(self):
    return {}


forms.BaseForm.get_formsets = get_formsets

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
    "formurlencodedentries": "Form URL Encoded",
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
        if self.schema:
            self.schema_json = json.dumps({c: self.schema[c].name for c in self.schema})

        super().__init__(*args, **kwargs)

        if self.fields.get("column"):
            self.fields["column"] = forms.ChoiceField(
                choices=create_column_choices(self.schema),
                help_text=self.base_fields["column"].help_text,
            )


# guarantee that widget attrs are updated after any changes in subclass __init__
class PostInitCaller(forms.models.ModelFormMetaclass):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__()
        return obj


class BaseModelForm(forms.ModelForm, metaclass=PostInitCaller):
    template_name = "django/forms/default_form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def __post_init__(self):
        for k, v in self.effect.items():
            self.fields[k].widget.attrs.update({"x-effect": v})

    @property
    def fields_json(self):
        return json.dumps(
            {
                field.name: field.value()
                for field in self
                if not isinstance(field.field, forms.FileField)
            }
            | {"computed": {}, "choices": {}}
        )

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

    @property
    def show(self):
        return self._meta.show

    @property
    def effect(self):
        return self._meta.effect


class LiveAlpineModelForm(BaseModelForm):
    def __init__(self, *args, **kwargs):
        self.parent_instance = kwargs.pop("parent_instance", None)
        super().__init__(*args, **kwargs)

        # filter to data populated by POST request in update
        # excluded fields are not rendered in the form
        if self.data:
            self.fields = {
                k: v
                for k, v in self.fields.items()
                if (f"{self.prefix}-{k}" if self.prefix else k) in self.data
            }


class LiveModelForm(BaseModelForm):
    ignore_live_update_fields = []

    def __init__(self, *args, **kwargs):
        self.parent_instance = kwargs.pop("parent_instance", None)
        super().__init__(*args, **kwargs)

        for field in self.ignore_live_update_fields:
            self.fields[field].widget.attrs.update({"data-live-update-ignore": ""})

        self.prefix = kwargs.get("prefix", None)

        # the rendered fields are determined by the values of the other fields
        # implementation designed to be overriden by subclass
        fields = self.get_live_fields()

        if self.is_live:
            self._errors = {}  # disable form validation
            self.data.update(self._get_live_data(fields))

        self.fields = {k: v for k, v in self.fields.items() if k in fields}

    def _get_field_data_key(self, field):
        # formset data is prefixed
        return f"{self.prefix}-{field}" if self.prefix else field

    def _get_live_data(self, fields):
        """Get the form data, falling back to initial or default values where
        the field was not displayed in the previous live form render."""

        data = MultiValueDict()

        for field in fields:
            key = self._get_field_data_key(field)
            value = self.get_live_field(field)

            # For HTML checkboxes, we need to distinguish two possibilities:
            # - the value of the checkbox is false (unchecked)
            # - the field was not displayed
            # Under the default HTML form implementation, these are indistinguishable.
            # Solution: we manually add the unchecked checkbox with "false" value

            if isinstance(self.fields[field], forms.BooleanField) and value == "false":
                continue

            # e.g. for an ArrayField, each item should be a separate value (rather than one value as a list)
            if isinstance(value, list):
                data.setlist(key, value)
            else:
                data[key] = value

        return data

    @property
    def is_live(self):
        # the "hidden_live" value is populated by the stimulus controller
        return "hidden_live" in self.data

    def get_live_field(self, field):
        """Return the current value of a field in a live form."""

        key = self._get_field_data_key(field)

        # data populated by POST request in update
        if key in self.data:
            return self.data[key]

        # fallback 1: initial value for form
        if field in self.initial:
            return self.initial[field]

        # fallback 2: default value for model field
        # used for formset placeholder rows where self.initial is empty
        initial = self.fields[field].initial
        return initial() if callable(initial) else initial

    def get_live_fields(self):
        """Return list of rendered fields derived from current form state.

        Designed to be overwritten by live form implementation. Default behaviour
        is a normal form (i.e. all fields)."""

        return list(self.fields.keys())

    @property
    def deleted(self):
        return self.data.get(f"{self.prefix}-DELETE") == "on"


class BaseLiveSchemaForm(SchemaFormMixin, LiveModelForm):
    pass


class BaseSchemaForm(SchemaFormMixin, BaseModelForm):
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
        if issubclass(formset.form, LiveModelForm) or issubclass(
            formset.form, LiveAlpineModelForm
        ):
            forms_kwargs["parent_instance"] = self.instance

        if issubclass(formset.form, SchemaFormMixin):
            forms_kwargs["schema"] = self.schema

        formset = (
            # POST request for form creation
            formset(
                self.data,
                self.files,
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


INPUT_SEARCH_THRESHOLD = 0.3


class IntegrationSearchMixin:
    def search_queryset(self, field, project, table_instance, used_ids):
        field.queryset = (
            Table.available.filter(project=project)
            .exclude(
                source__in=[Table.Source.INTERMEDIATE_NODE, Table.Source.CACHE_NODE]
            )
            .annotate(
                is_used_in=Case(
                    When(id__in=used_ids, then=True),
                    default=False,
                ),
            )
            .order_by("updated")
        )
        if search := self.data.get("search"):
            field.queryset = (
                field.queryset.annotate(
                    similarity=Greatest(
                        TrigramSimilarity("integration__name", search),
                        TrigramSimilarity("workflow_node__workflow__name", search),
                        TrigramSimilarity("bq_table", search),
                    )
                )
                .filter(
                    Q(similarity__gte=INPUT_SEARCH_THRESHOLD)
                    | Q(id=getattr(table_instance, "id", None))
                )
                .order_by("-similarity")
            )
