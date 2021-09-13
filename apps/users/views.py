import analytics
from allauth.account.utils import send_email_confirmation
from allauth.socialaccount.providers.google.views import oauth2_login
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST

from apps.base.mixins import PageTitleMixin
from apps.base.analytics import ONBOARDING_COMPLETED_EVENT
from apps.base.turbo import TurboUpdateView

from .forms import (
    CustomUserChangeForm,
    UploadAvatarForm,
    UserOnboardingForm,
    UserNameForm
)
from .helpers import (require_email_confirmation,
                      user_has_confirmed_email_address)
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

    def form_valid(self, form):
        redirect = super().form_valid(form)
        return redirect

    def get_success_url(self) -> str:
        user = self.request.user

        if user.first_name == "" or user.last_name == "":
            return reverse("users:onboarding")

        if not user.company_industry or not user.company_role or not user.company_size:
            return reverse("users:onboarding")

        analytics.track(self.request.user.id, ONBOARDING_COMPLETED_EVENT)
        return reverse("web:home")


class UserProfile(PageTitleMixin, TurboUpdateView):
    template_name = "account/profile.html"
    model = CustomUser
    form_class = CustomUserChangeForm
    success_url = reverse_lazy("users:user_profile")
    page_title = "Your Account"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form) -> HttpResponse:
        user = form.save(commit=False)
        user_before_update = CustomUser.objects.get(pk=user.pk)
        need_to_confirm_email = (
            user_before_update.email != user.email
            and require_email_confirmation()
            and not user_has_confirmed_email_address(user, user.email)
        )
        if need_to_confirm_email:
            # don't change it but instead send a confirmation email
            # email will be changed by signal when confirmed
            new_email = user.email
            send_email_confirmation(self.request, user, signup=False, email=new_email)
            user.email = user_before_update.email

        return super().form_valid(form)


@require_POST
def upload_profile_image(request):
    user = request.user
    form = UploadAvatarForm(request.POST, request.FILES)
    if form.is_valid():
        user.avatar = request.FILES["avatar"]
        user.save()
    return HttpResponse("Success!")
