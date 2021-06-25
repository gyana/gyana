import analytics
from apps.utils.segment_analytics import SIGNED_UP_EVENT, identify_user
from allauth.account.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import HiddenInput

from .models import Invitation, Team


class TeamSignupForm(SignupForm):
    invitation_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean_invitation_id(self):
        invitation_id = self.cleaned_data.get("invitation_id")
        if invitation_id:
            try:
                invite = Invitation.objects.get(id=invitation_id)
                if invite.is_accepted:
                    raise forms.ValidationError(
                        _(
                            "It looks like that invitation link has expired. "
                            "Please request a new invitation or sign in to continue."
                        )
                    )
            except (Invitation.DoesNotExist, ValidationError):
                # ValidationError is raised if the ID isn't a valid UUID, which should be treated the same
                # as not found
                raise forms.ValidationError(
                    _(
                        "That invitation could not be found. "
                        "Please double check your invitation link or sign in to continue."
                    )
                )
        return invitation_id

    def save(self, request):
        user = super().save(request)
        identify_user(user)

        analytics.track(user.id, SIGNED_UP_EVENT)

        return user


class TeamChangeForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name", "slug")
        help_texts = {
            "slug": "Your team slug is what appears in the various URLs your team uses. No spaces or special characters are allowed."
        }
