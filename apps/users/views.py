import analytics
import jwt
from allauth.account.utils import send_email_confirmation
from allauth.socialaccount.providers.google.views import oauth2_login
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic.base import View

from apps.base.analytics import ONBOARDING_COMPLETED_EVENT
from apps.base.mixins import PageTitleMixin
from apps.base.turbo import TurboUpdateView

from .forms import CustomUserChangeForm, UserNameForm, UserOnboardingForm
from .helpers import require_email_confirmation, user_has_confirmed_email_address
from .models import CustomUser


def appsumo_oauth2_login(request, *args, **kwargs):
    request.session["socialaccount_appsumo"] = "appsumo" in request.GET
    return oauth2_login(request, *args, **kwargs)


class UserOnboarding(PageTitleMixin, TurboUpdateView):
    template_name = "users/onboarding.html"
    model = CustomUser
    page_title = "Onboarding"

    def get_form_class(self):
        if self.request.user.first_name == "":
            return UserNameForm

        return UserOnboardingForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self) -> str:
        user = self.request.user

        if user.first_name == "" or user.last_name == "":
            return reverse("users:onboarding")

        if not user.company_industry or not user.company_role or not user.company_size:
            return reverse("users:onboarding")

        analytics.track(self.request.user.id, ONBOARDING_COMPLETED_EVENT)
        return reverse("web:home")


class UserFeedback(View):
    def get(self, request, *args, **kwargs):
        # https://hellonext.co/help/sso-redirects

        encoded_jwt = jwt.encode(
            {
                "email": request.user.email,
                "name": request.user.get_full_name() or request.user.username,
            },
            settings.HELLONEXT_SSO_TOKEN,
            algorithm="HS256",
        )

        url = f"https://app.hellonext.co/redirects/sso?domain={request.GET['domain']}&ssoToken={encoded_jwt}&redirect={request.GET['redirect']}"

        return redirect(url)
