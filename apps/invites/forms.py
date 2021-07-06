from django import forms
from django.utils.translation import ugettext_lazy as _

from invitations.forms import CleanEmailMixin

from .models import Invite


class InviteForm(forms.Form, CleanEmailMixin):
    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"}),
        initial="",
    )

    def save(self, email, team):
        return Invite.create(email=email, team=team, role="member")
