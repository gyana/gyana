from allauth.account.utils import send_email_confirmation
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import UpdateView
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse

from apps.base.mixins import PageTitleMixin
from apps.users.helpers import (
    require_email_confirmation,
    user_has_confirmed_email_address,
)

from .forms import CustomUserChangeForm
from .models import CustomUser


class UserProfileModal(PageTitleMixin, UpdateView):
    template_name = "account/profile.html"
    model = CustomUser
    form_class = CustomUserChangeForm
    page_title = "Your Account"

    def get_turbo_stream_response(self, context):
        context = self.get_context_data()
        return TurboStreamResponse(
            [
                TurboStream(self.turbo_frame_dom_id)
                .replace.template(self.template_name, context)
                .render()
            ]
        )

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

    def get_success_url(self) -> str:
        return reverse("users:profile")
