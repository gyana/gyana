from django import forms
from django.db import transaction


class BaseModelForm(forms.ModelForm):
    def on_save(self, instance):
        # override in child to add behaviour on commit save
        pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit == True:
            with transaction.atomic():
                self.on_save(instance)
                instance.save()
                self.save_m2m()
        return instance
