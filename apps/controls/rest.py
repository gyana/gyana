from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import ControlWidget
from .serializers import ControlWidgetSerializer


class ControlWidgetPartialUpdate(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    serializer_class = ControlWidgetSerializer
    permission_classes = (IsAuthenticated,)
    # Overwriting queryset to prevent access to control-widgets that don't belong to
    # the user's team
    def get_queryset(self):
        # To create schema this is called without a request
        if self.request is None:
            return ControlWidget.objects.none()
        return ControlWidget.objects.filter(
            page__dashboard__project__team__in=self.request.user.teams.all()
        ).all()
