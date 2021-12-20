from django import forms

from apps.base.forms import BaseModelForm

from .models import OAuth2


class OAuth2CreateForm(BaseModelForm):
    class Meta:
        model = OAuth2
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.project = self._project


class OAuth2UpdateForm(forms.ModelForm):
    class Meta:
        model = OAuth2
        fields = [
            "name",
            "client_id",
            "client_secret",
            "authorization_base_url",
            "token_url",
            "scope",
        ]
        labels = {
            "client_id": "Client ID",
            "client_secret": "Client Secret",
            "authorization_base_url": "Auth URL",
            "token_url": "Access Token URL",
        }
