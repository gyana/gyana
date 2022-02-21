from allauth.account.utils import send_email_confirmation
from django.http import HttpResponse
from django.urls import reverse_lazy

from apps.base.frames import TurboFrameUpdateView
from apps.base.mixins import PageTitleMixin
from apps.users.helpers import (
    require_email_confirmation,
    user_has_confirmed_email_address,
)

from .forms import CustomUserChangeForm
from .models import CustomUser


class UserProfileModal(PageTitleMixin, TurboFrameUpdateView):
    template_name = "account/profile.html"
    model = CustomUser
    form_class = CustomUserChangeForm
    success_url = reverse_lazy("users:profile")
    page_title = "Your Account"
    turbo_frame_dom_id = "users:profile"

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
