from apps.base.forms import BaseModelForm

from .models import Table


class TableForm(BaseModelForm):
    class Meta:
        model = Table
        fields = []
