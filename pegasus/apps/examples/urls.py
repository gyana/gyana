from django.urls import path
from django.views.generic import TemplateView
from rest_framework import routers

from . import views

app_name = "pegasus_examples"

urlpatterns = [
    path("", views.ExamplesHomeView.as_view(), name="examples_home"),
    path("payments", views.PaymentView.as_view(), name="payments"),
    path(
        "payments/create_payment_intent/",
        views.create_payment_intent,
        name="create_payment_intent",
    ),
    path("payments/create/", views.accept_payment, name="accept_payment"),
    path(
        "payments/confirm/<slug:payment_id>/",
        views.payment_confirm,
        name="payment_confirm",
    ),
    path(
        "landing_page/",
        TemplateView.as_view(
            template_name="pegasus/examples/example_landing_page.html"
        ),
        name="landing_page",
    ),
    path(
        "pricing_page/",
        TemplateView.as_view(
            template_name="pegasus/examples/example_pricing_page.html"
        ),
        name="pricing_page",
    ),
    path(
        "objects/react/",
        views.ReactObjectLifecycleView.as_view(),
        name="react_object_lifecycle",
    ),
    path(
        "objects/react/<path:path>",
        views.ReactObjectLifecycleView.as_view(),
        name="react_object_lifecycle_w_path",
    ),
    path("charts/", views.ChartsView.as_view(), name="charts"),
    path("tasks/", views.TasksView.as_view(), name="tasks"),
    path("tasks/api/", views.tasks_api, name="tasks_api"),
    path(
        "api/employee-data/", views.EmployeeDataAPIView.as_view(), name="employee_data"
    ),
]


# drf config
router = routers.DefaultRouter()
router.register("api/employees", views.EmployeeViewSet)

urlpatterns += router.urls
