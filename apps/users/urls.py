from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path("profile/", login_required(views.profile), name="user_profile"),
    path(
        "profile/upload-image/",
        login_required(views.upload_profile_image),
        name="upload_profile_image",
    ),
]
