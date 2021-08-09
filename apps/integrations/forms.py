from apps.connectors.forms import FivetranForm
from apps.sheets.forms import SheetCreateForm
from django import forms

from .models import Integration


class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name"]
