from apps.base.clients import heroku_client
from django import forms
from django.db import transaction

from .models import CName


class CNameForm(forms.ModelForm):
    class Meta:
        model = CName
        fields = ["domain"]

    def __init__(self, *args, **kwargs):
        self._team = kwargs.pop("team")
        return super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.team = self._team

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()

        heroku_client().add_domain(instance.domain)

        return instance
