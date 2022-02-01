from django.urls import path

from . import views

app_name = "learn"
urlpatterns = [
    path("search", views.Search.as_view(), name="search"),
]
