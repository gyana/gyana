from django import forms
from django.utils.datastructures import MultiValueDict


class LiveUpdateForm(forms.ModelForm):

    hidden_live = forms.CharField(widget=forms.HiddenInput(), required=True)

    def update_data(self):
        data = MultiValueDict({**self.data})
        for field in self.get_live_fields():
            if (
                field not in self.data
                and self.initial.get(field)
                and not isinstance(self.fields[field], forms.BooleanField)
            ):
                data[field] = self.initial[field]

            elif (
                isinstance(self.fields[field], forms.BooleanField)
                and self.data.get(field) == "false"
            ):
                data.pop(field)

        self.data = data

    def __init__(self, *args, **kwargs):

        self.parent_instance = kwargs.pop("parent_instance", None)

        super().__init__(*args, **kwargs)
        # self.data = MultiValueDict(
        #     {**{key: [value] for key, value in self.initial.items()}, **self.data}
        # )

        self.prefix = kwargs.pop("prefix", None)

        # the rendered fields are determined by the values of the other fields
        live_fields = self.get_live_fields()
        self.update_data()
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

        # formset data is prefixed
        key_ = f"{self.prefix}-{name}" if self.prefix else name

        # data populated by POST request in update
        # is also populated by initial data from the database
        # in the init method
        return (
            self.data.get(key_)
            or self.initial.get(key_)
            or getattr(self.instance, name)
        )

    def get_live_fields(self):
        # by default the behaviour is a normal form
        return [f for f in self.fields.keys() if f != "hidden_live"]
