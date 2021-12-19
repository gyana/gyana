from django import forms

from .models import OAuth2


class OAuth2Form(forms.ModelForm):
    class Meta:
        model = OAuth2
        fields = [
            "name",
            "client_id",
            "client_secret",
            "authorization_base_url",
            "token_url",
            "scope"
        ]
        labels = {
            "client_id": "Client ID",
            "client_secret": "Client Secret",
            "authorization_base_url": "Auth URL",
            "token_url": "Access Token URL",
        }
