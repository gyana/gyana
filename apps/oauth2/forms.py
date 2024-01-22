from django import forms

from apps.base.forms import ModelForm

from .models import OAuth2


class OAuth2CreateForm(ModelForm):
    class Meta:
        model = OAuth2
        fields = ["name"]
        help_texts = {"name": "The name of the service, to help you remember it"}

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.project = self._project


class OAuth2UpdateForm(ModelForm):
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
        widgets = {"client_secret": forms.PasswordInput(render_value=True)}
        labels = {
            "client_id": "Client ID",
            "client_secret": "Client Secret",
            "authorization_base_url": "Authorization URL",
            "token_url": "Token URL",
        }
        help_texts = {
            "authorization_base_url": "The authorization URL for your provider, e.g. https://github.com/login/oauth/authorize",
            "token_url": "The token URL for your provider, e.g. https://github.com/login/oauth/access_token",
            "scope": "Define what you get access to, required for some services, e.g. repo,gist",
        }
