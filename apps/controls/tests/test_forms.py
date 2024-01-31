import pytest

from apps.controls.forms import ControlForm

pytestmark = pytest.mark.django_db


def test_control_form(pwf):
    form = ControlForm()

    pwf.render(form)
    pwf.assert_fields({"date_range"})

    pwf.select_value("date_range", "custom")
    pwf.assert_fields({"date_range", "start", "end"})
