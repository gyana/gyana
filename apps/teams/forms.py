import analytics
from allauth.account.forms import SignupForm
from apps.base.segment_analytics import SIGNED_UP_EVENT, identify_user
from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Membership, Team


class TeamSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(TeamSignupForm, self).__init__(*args, **kwargs)

        del self.fields['email'].widget.attrs['placeholder']
        del self.fields['password1'].widget.attrs['placeholder']

        self.fields['email'].help_text = "e.g. maryjackson@nasa.gov"
        self.fields['password1'].help_text = "Must have at least 6 characters"


    def save(self, request):
        user = super().save(request)
        identify_user(user)

        analytics.track(user.id, SIGNED_UP_EVENT)

        return user


class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name",)


class TeamUpdateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name",)


class MembershipUpdateForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ("role",)
