from django import forms

from .models import CName


class CNameForm(forms.ModelForm):
    class Meta:
        model = CName
        fields = ["domain"]
