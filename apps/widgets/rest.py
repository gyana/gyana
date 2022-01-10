from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.widgets.serializers import WidgetSerializer

from .models import Widget


class WidgetPartialUpdate(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    serializer_class = WidgetSerializer
    permission_classes = (IsAuthenticated,)

    # Overwriting queryset to prevent access to widgets that don't belong to
    # the user's team
    def get_queryset(self):

        # To create schema this is called without a request
        if self.request is None:
            return Widget.objects.all()
        return Widget.objects.filter(
            page__dashboard__project__team__members=self.request.user
        ).all()
