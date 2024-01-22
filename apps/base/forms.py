import json
from contextlib import contextmanager
from functools import cache

from crispy_forms import utils
from crispy_forms.helper import FormHelper
from django import forms
from django.db import transaction
from django.forms.models import ModelFormOptions

from apps.base.core.utils import create_column_choices


# By default, django-crispy-form caches the template, breaking hot-reloading in development
def default_field_template(template_pack=utils.TEMPLATE_PACK):
    return utils.get_template("%s/field.html" % template_pack)


utils.default_field_template = default_field_template

ModelFormOptions__init__ = ModelFormOptions.__init__


def __init__(self, options=None):
    ModelFormOptions__init__(self, options=options)
    self.formsets = getattr(options, "formsets", {})
    self.show = getattr(options, "show", None)
    self.effect = getattr(options, "effect", {})


ModelFormOptions.__init__ = __init__


def get_formsets(self):
    return {}


forms.BaseForm.get_formsets = get_formsets


# guarantee that widget attrs are updated after any changes in subclass __init__
class PostInitCaller(forms.models.ModelFormMetaclass):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__()
        return obj


class BaseModelForm(forms.ModelForm, metaclass=PostInitCaller):
    template_name = "django/forms/default_form.html"

    def __init__(self, *args, **kwargs):
        self.parent_instance = kwargs.pop("parent_instance", None)
        self.schema = kwargs.pop("schema", None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.render_hidden_fields = True

        # TODO: add a custom field/widget for this if possible
        if self.fields.get("column"):
            self.fields["column"] = forms.ChoiceField(
                choices=create_column_choices(self.schema),
                help_text=self.base_fields["column"].help_text,
            )

    def __post_init__(self):
        for k, v in self.effect.items():
            self.fields[k].widget.attrs.update({"x-effect": v})

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

    @property
    def formsets(self):
        return self._meta.formsets


class AlpineMixin:
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

    def schema_json(self):
        if self.schema:
            return json.dumps({c: self.schema[c].name for c in self.schema})

    # only clean/validate/save fields rendered in the form
    # but keep track of all fields if form is invalid and is re-rendered
    @contextmanager
    def alpine_fields(self):
        all_fields = self.fields
        self.fields = {
            k: v
            for k, v in self.fields.items()
            if (f"{self.prefix}-{k}" if self.prefix else k) in self.data
        }
        yield
        self.fields = all_fields

    @property
    def errors(self):
        with self.alpine_fields():
            return super().errors

    def save(self, commit=True):
        with self.alpine_fields():
            return super().save(commit)

    def save_m2m(self, commit=True):
        with self.alpine_fields():
            return super().save_m2m(commit)


class LiveFormsetMixin:
    def get_formset_kwargs(self, formset):
        return {}

    def get_formset_form_kwargs(self, formset):
        return {}

    def get_formset(self, prefix, formset):
        forms_kwargs = self.get_formset_form_kwargs(formset)

        # provide a reference to parent instance in live update forms
        forms_kwargs["parent_instance"] = self.instance

        if self.schema:
            forms_kwargs["schema"] = self.schema

        formset = (
            # POST request for form creation
            formset(
                self.data,
                self.files,
                instance=self.instance,
                **self.get_formset_kwargs(formset),
                form_kwargs=forms_kwargs,
                prefix=prefix,
            )
            # form is only bound if formset is in previous render, otherwise load from database
            if self.data and f"{prefix}-TOTAL_FORMS" in self.data
            # initial render
            else formset(
                instance=self.instance,
                **self.get_formset_kwargs(formset),
                form_kwargs=forms_kwargs,
                prefix=prefix,
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
        return {k: self.get_formset(k, v) for k, v in self.formsets.items()}


class ModelForm(LiveFormsetMixin, AlpineMixin, BaseModelForm):
    pass
