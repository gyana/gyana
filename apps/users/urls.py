from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.defaults import page_not_found
from django.views.generic.base import RedirectView
from turbo_allauth.views import account

from apps.base.clickjacking import xframe_options_sameorigin_allowlist

from . import frames, views

app_name = "users"
urlpatterns = [
    path(
        "onboarding/",
        login_required(views.UserOnboarding.as_view()),
        name="onboarding",
    ),
    path("feedback", login_required(views.UserFeedback.as_view()), name="feedback"),
    # Trubo frames
    path("profile", login_required(frames.UserProfileModal.as_view()), name="profile"),
]

accounts_urlpatterns = [
    # https://github.com/pennersr/django-allauth/issues/1109
    path(
        "email/",
        page_not_found,
        {"exception": Exception("Not Found")},
        name="account_email",
    ),
    # Redirecting old signin link to account_login
    # SHUTDOWN: disable signup and signin
    path("signup/", page_not_found, {"exception": Exception()}),
    path("signin/", page_not_found, {"exception": Exception()}),
    path("login/", page_not_found, {"exception": Exception()}),
    # path("signin/", RedirectView.as_view(pattern_name="account_login")),
    # path(
    #     "signup/",
    #     xframe_options_sameorigin_allowlist(views.AccountSignupView.as_view()),
    #     name="account_signup",
    # ),
    path("", include("turbo_allauth.urls")),
]
