from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.defaults import page_not_found

from . import views

app_name = "users"
urlpatterns = [
    path(
        "onboarding/",
        login_required(views.UserOnboarding.as_view()),
        name="onboarding",
    ),
    path("profile/", login_required(views.UserProfile.as_view()), name="user_profile"),
    path(
        "profile/upload-image/",
        login_required(views.upload_profile_image),
        name="upload_profile_image",
    ),
]

accounts_urlpatterns = [
    # https://github.com/pennersr/django-allauth/issues/1109
    path(
        "email/",
        page_not_found,
        {"exception": Exception("Not Found")},
        name="account_email",
    ),
    path(
        "google/login/",
        views.appsumo_oauth2_login,
        name="google_login",
    ),
    path("", include("turbo_allauth.urls")),
]
