from django.urls import include, path
from django.views.decorators.cache import cache_control

from .. import views

app_name = "widgets"
urlpatterns = [
    path("", views.WidgetList.as_view(), name="list"),
    path("new", views.WidgetCreate.as_view(), name="create"),
    path("<int:pk>", views.WidgetDetail.as_view(), name="detail"),
    path("<int:pk>/update", views.WidgetUpdate.as_view(), name="update"),
    path("<int:pk>/delete", views.WidgetDelete.as_view(), name="delete"),
]
