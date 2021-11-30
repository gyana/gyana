from django import forms
from django.db import transaction

from apps.base.schema_form_mixin import SchemaFormMixin


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


class BaseSchemaForm(SchemaFormMixin, forms.ModelForm):
    pass
