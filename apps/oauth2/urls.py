from django.urls import path

from . import views

app_name = "oauth2"

urlpatterns = [
    path(
        "<hashid:pk>/login",
        views.OAuth2Login.as_view(),
        name="login",
    ),
    path(
        "<hashid:pk>/callback",
        views.OAuth2Callback.as_view(),
        name="callback",
    ),
]

project_urlpatterns = (
    [
        path("", views.OAuth2List.as_view(), name="list"),
        path("new", views.OAuth2Create.as_view(), name="create"),
        path("<hashid:pk>", views.OAuth2Detail.as_view(), name="detail"),
        path("<hashid:pk>/update", views.OAuth2Update.as_view(), name="update"),
        path("<hashid:pk>/delete", views.OAuth2Delete.as_view(), name="delete"),
    ],
    "project_integrations",
)
