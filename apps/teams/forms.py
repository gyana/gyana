import analytics
from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.utils.html import mark_safe
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from apps.base.analytics import (
    SIGNED_UP_EVENT,
    TEAM_CREATED_EVENT,
    identify_user,
    identify_user_group,
)
from apps.base.forms import BaseModelForm
from apps.base.live_update_form import LiveUpdateForm
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

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data["email"].lower()

        self._waitlist_approved = ApprovedWaitlistEmail.check_approved(email)
        self._accepted_invite = Invite.check_email_accepted(email)

        if not self._waitlist_approved and not self._accepted_invite:
            raise forms.ValidationError(
                mark_safe(
                    'Gyana is currently invite only. <a href="https://www.gyana.com" class="link">Join our waitlist.</a>'
                )
            )

    def save(self, request):
        user = super().save(request)
        # prefer to assign as an invite than a waitlist
        if self._accepted_invite:
            identify_user(user, signup_source="invite")
        elif self._waitlist_approved:
            identify_user(user, signup_source="waitlist")

        analytics.track(user.id, SIGNED_UP_EVENT)

        return user


class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name",)
        labels = {"name": "Name your team"}
        help_texts = {"name": "We recommend you use the name of your organisation"}

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


class TeamSubscriptionForm(LiveUpdateForm):
    class Meta:
        model = Team
        fields = ()

    plan = forms.ChoiceField(
        label="Your plan",
        help_text=mark_safe(
            '<a href="https://www.gyana.com/pricing" class="link">Learn more</a> on our website.'
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].choices = (
            (settings.DJPADDLE_PRO_PLAN_ID, "Pro"),
            (settings.DJPADDLE_BUSINESS_PLAN_ID, "Business"),
        )

    def post_save(self, instance):
        update_plan_for_team(instance, int(self.cleaned_data["plan"]))
        return super().post_save(instance)
