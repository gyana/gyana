import analytics
from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.utils.html import mark_safe
from django.utils.safestring import mark_safe

from apps.base.analytics import (
    SIGNED_UP_EVENT,
    TEAM_CREATED_EVENT,
    identify_user,
    identify_user_group,
)
from apps.base.forms import BaseModelForm, LiveModelForm
from apps.base.templatetags.help_utils import INTERCOM_ROOT, get_intercom
from apps.invites.models import Invite
from apps.teams import roles
from apps.users.models import ApprovedWaitlistEmail

from .models import Flag, Membership, Team
from .paddle import update_plan_for_team


class TeamSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(TeamSignupForm, self).__init__(*args, **kwargs)

        del self.fields["email"].widget.attrs["placeholder"]
        del self.fields["password1"].widget.attrs["placeholder"]

        self.fields["email"].help_text = "e.g. maryjackson@nasa.gov"
        self.fields["password1"].help_text = "Must have at least 6 characters"

    def save(self, request):
        user = super().save(request)
        # prefer to assign as an invite than a waitlist
        if Invite.check_email_invited(user.email):
            identify_user(user, signup_source="invite")
        elif ApprovedWaitlistEmail.check_approved(user.email):
            identify_user(user, signup_source="waitlist")
        else:
            identify_user(user, signup_source="website")

        analytics.track(user.id, SIGNED_UP_EVENT)

        return user


class TeamCreateForm(BaseModelForm):
    class Meta:
        model = Team
        fields = ("name",)
        labels = {"name": "Name your team"}
        help_texts = {"name": "We recommend you use the name of your organisation"}

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def post_save(self, instance):
        instance.members.add(self._user, through_defaults={"role": "admin"})

        analytics.track(self._user.id, TEAM_CREATED_EVENT)
        identify_user_group(self._user, instance)


class TeamUpdateForm(BaseModelForm):
    class Meta:
        model = Team
        fields = ("icon", "name", "timezone")
        widgets = {"icon": forms.ClearableFileInput(attrs={"accept": "image/*"})}
        help_texts = {
            "icon": "For best results use a square image",
            "timezone": "We use this to display time information and to schedule workflows",
        }

    beta = forms.BooleanField(
        required=False,
        label="Join Beta",
        help_text=mark_safe(
            f"""Turn on early access to new features from our beta program. <a href="{INTERCOM_ROOT}/{get_intercom()['overview']['beta']}" target="_blank" class="link">Learn more</a>."""
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["beta"].initial = Flag.check_team_in_beta(self.instance)

    def pre_save(self, instance):
        self._timezone_is_dirty = "timezone" in instance.get_dirty_fields()

    def post_save(self, instance):
        if self._timezone_is_dirty:
            instance.update_daily_sync_time()

        Flag.set_beta_program_for_team(instance, self.cleaned_data["beta"])


class MembershipUpdateForm(BaseModelForm):
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
