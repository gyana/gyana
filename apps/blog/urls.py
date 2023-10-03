from django.urls import path

from . import views

app_name = "blog"
urlpatterns = [
    path("", views.PostList.as_view(), name="list"),
    path("<str:slug>", views.PostDetail.as_view(), name="detail"),
]
