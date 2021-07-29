from django import forms
from django.utils.datastructures import MultiValueDict


class LiveUpdateForm(forms.ModelForm):

    hidden_live = forms.CharField(widget=forms.HiddenInput(), required=True)

    def _update_data_with_initial(self):
        """Updates the form's data missing fields with the initial values.

        Because LiveForms don't hold data for fields that haven't been displayed,
        we need to manually add these values."""
        # self.data hold data from request.POST and can be a MultiValueDict or a QueryDict
        data = MultiValueDict({**self.data})
        for field in self.get_live_fields():
            # self.initial is a dict holding the model data that
            # For the additional formset rows that added as placeholders
            # self.initial is empty.
            if field not in self.data and self.initial.get(field) is not None:
                data[field] = self.initial[field]
            # HTML forms usually just omit unchecked checkboxes
            # For us this is undistinguishable from the field not having been shown before
            # In the LiveFormController we manually add these fields to the form data
            # Just to remove them here again
            elif (
                isinstance(self.fields[field], forms.BooleanField)
                and self.data.get(field) == "false"
            ):
                data.pop(field)

        self.data = data

    def __init__(self, *args, **kwargs):

        self.parent_instance = kwargs.pop("parent_instance", None)

        super().__init__(*args, **kwargs)

        self.prefix = kwargs.pop("prefix", None)

        # the rendered fields are determined by the values of the other fields
        live_fields = self.get_live_fields()
        self._update_data_with_initial()
        # - when the Stimulus controller makes a POST request, it will always be invalid
        # and re-render the same form with the updated values
        # - when the form is valid and the user clicks a submit button, the live field is
        # not rendered and it behaves like a normal form
        if self.is_live:
            live_fields += ["hidden_live"]
        self.fields = {k: v for k, v in self.fields.items() if k in live_fields}

    @property
    def is_live(self):
        # the "submit" value is populated when the user clicks the button
        return "submit" not in self.data

    def get_live_field(self, name):
        # potentially called before self._update_data_with_initial
        # formset data is prefixed
        key_ = f"{self.prefix}-{name}" if self.prefix else name

        # data populated by POST request in update
        # as a fallback we are using the database value

        return self.data.get(key_) or getattr(self.instance, name)

    def get_live_fields(self):
        # by default the behaviour is a normal form
        return [f for f in self.fields.keys() if f != "hidden_live"]
