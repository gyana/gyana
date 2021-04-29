from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.templatetags.static import static
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Employee
from ..serializers import EmployeeSerializer


@method_decorator(login_required, name="dispatch")
class ObjectLifecycleView(TemplateView):
    def get_context_data(self, **kwargs):
        return {
            "department_choices": [
                {"id": c[0], "name": c[1]} for c in Employee.DEPARTMENT_CHOICES
            ],
        }


class ReactObjectLifecycleView(ObjectLifecycleView):
    template_name = "pegasus/examples/objects/react_object_lifecycle.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "framework_url": "https://reactjs.org/",
                "framework_name": "React",
                "framework_icon": static("images/pegasus/react-icon.png"),
                "active_tab": "react_object_lifecycle",
            }
        )
        return context


@method_decorator(login_required, name="dispatch")
class ChartsView(TemplateView):
    template_name = "pegasus/examples/objects/charts.html"

    def get_context_data(self, **kwargs):
        return {
            "active_tab": "charts",
        }


class EmployeeDataAPIView(APIView):
    def get(self, request):
        data = request.user.employees.values("department").annotate(
            average_salary=Avg("salary"),
            total_cost=Sum("salary"),
            number_employees=Count("pk"),
        )
        # data will look something like this:
        # [
        #     {'total_cost': 132000, 'number_employees': 2, 'average_salary': 66000.0, 'department': 'hr'},
        #     {'total_cost': 60000, 'number_employees': 1, 'average_salary': 60000.0, 'department': 'marketing'}
        # ]
        total_costs = [[row["department"], row["total_cost"]] for row in data]
        average_salaries = [[row["department"], row["average_salary"]] for row in data]
        headcounts = [[row["department"], row["number_employees"]] for row in data]
        return Response(
            {
                "total_costs": total_costs,
                "average_salaries": average_salaries,
                "headcounts": headcounts,
            }
        )


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        # filter queryset based on logged in user
        return self.request.user.employees.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
