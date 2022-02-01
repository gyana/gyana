import pytest
import wagtail_factories
from pytest_factoryboy import register

from apps.learn.models import LearnPage

pytestmark = pytest.mark.django_db


@register
class LearnPageFactory(wagtail_factories.PageFactory):
    title = "Gyana University"
    body = []
    slug = "learn"
    show_in_menus = True

    class Meta:
        model = LearnPage
