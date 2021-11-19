from allauth.account.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.defaults import page_not_found
from django.views.generic.base import RedirectView

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
    path("settings", login_required(frames.UserSettingsModal.as_view()), name="settings"),
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
    path("signin/", RedirectView.as_view(pattern_name="account_login")),
    path("", include("turbo_allauth.urls")),
]
