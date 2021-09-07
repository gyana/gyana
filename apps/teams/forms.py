import analytics
from allauth.account.forms import SignupForm
from django import forms
from django.utils.translation import ugettext_lazy as _

from apps.base.analytics import (
    SIGNED_UP_EVENT,
    TEAM_CREATED_EVENT,
    identify_user,
    identify_user_group,
)
from apps.teams import roles

from .models import Membership, Team


class TeamSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(TeamSignupForm, self).__init__(*args, **kwargs)

        del self.fields["email"].widget.attrs["placeholder"]
        del self.fields["password1"].widget.attrs["placeholder"]

        self.fields["email"].help_text = "e.g. maryjackson@nasa.gov"
        self.fields["password1"].help_text = "Must have at least 6 characters"

    def save(self, request):
        user = super().save(request)
        identify_user(user)

        analytics.track(user.id, SIGNED_UP_EVENT)

        return user


class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name",)
        labels = {"name": "Name your team"}
        help_texts = {
            "name": "We recommend you use the name of your organisation, you can change it later"
        }

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()
            instance.members.add(self._user, through_defaults={"role": "admin"})
            self.save_m2m()

        analytics.track(self._user.id, TEAM_CREATED_EVENT)
        identify_user_group(self._user, instance)

        return instance


class TeamUpdateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name",)


class MembershipUpdateForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ("role",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Prevent last admin turning to member
        if self.instance.role == roles.ROLE_ADMIN and not self.instance.can_delete:
            self.fields["role"].widget.attrs["disabled"] = True
            self.fields[
                "role"
            ].help_text = (
                "You cannot make yourself a member because there is no admin left"
            )
