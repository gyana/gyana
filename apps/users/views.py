import analytics
from allauth.account.utils import send_email_confirmation
from allauth.socialaccount.providers.google.views import oauth2_login
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from apps.base.analytics import ONBOARDING_COMPLETED_EVENT
from apps.base.turbo import TurboUpdateView

from .forms import CustomUserChangeForm, UploadAvatarForm, UserOnboardingForm
from .helpers import (require_email_confirmation,
                      user_has_confirmed_email_address)
from .models import CustomUser


def appsumo_oauth2_login(request, *args, **kwargs):
    request.session["socialaccount_appsumo"] = "appsumo" in request.GET
    return oauth2_login(request, *args, **kwargs)


class UserOnboarding(TurboUpdateView):
    template_name = "users/onboarding.html"
    model = CustomUser
    form_class = UserOnboardingForm
    success_url = reverse_lazy("web:home")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        redirect = super().form_valid(form)
        analytics.track(self.request.user.id, ONBOARDING_COMPLETED_EVENT)
        return redirect


class UserProfile(TurboUpdateView):
    template_name = "account/profile.html"
    model = CustomUser
    form_class = CustomUserChangeForm
    success_url = reverse_lazy("users:user_profile")

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
