from django import forms

from .models import Invite


class InviteForm(forms.ModelForm):
    class Meta:
        model = Invite
        fields = ["email", "role"]
