import analytics
import jwt
from allauth.account.views import SignupView
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.base import View

from apps.base.analytics import ONBOARDING_COMPLETED_EVENT
from apps.base.mixins import PageTitleMixin
from apps.base.views import TurboUpdateView

from .forms import UserNameForm, UserOnboardingForm
from .models import CustomUser


class AccountSignupView(SignupView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if "email" in self.request.GET:
            kwargs["initial"]["email"] = self.request.GET.get("email")
        return kwargs


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
