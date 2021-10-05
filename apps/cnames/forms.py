from apps.base.clients import heroku_client
from apps.base.forms import BaseModelForm

from .models import CName


class CNameForm(BaseModelForm):
    class Meta:
        model = CName
        fields = ["domain"]

    def __init__(self, *args, **kwargs):
        self._team = kwargs.pop("team")
        return super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.team = self._team

    def post_save(self, instance):
        heroku_client().add_domain(instance.domain)
