from apps.controls.forms import ControlForm


def test_control_form(pwf):
    form = ControlForm()

    pwf.render(form)
    pwf.assert_fields({"date_range"})

    pwf.select_value("date_range", "custom")
    pwf.assert_fields({"date_range", "start", "end"})
