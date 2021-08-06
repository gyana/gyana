from django import forms

from .models import Connector


class ConnectorForm(forms.ModelForm):
    class Meta:
        model = Connector
        fields = ['name']
