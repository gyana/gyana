from model_clone import CloneMixin


# Class name matters because double underscore is replaced
# by classname
class CloneMixin(CloneMixin):
    # TODO: Because of an issue https://github.com/tj-django/django-clone/issues/549
    # we need to make the expression falsy
    _clone_excluded_fields = [""]
    _clone_excluded_m2m_fields = [""]
    _clone_excluded_m2o_or_o2m_fields = [""]
    _clone_excluded_o2o_fields = [""]

    def __duplicate_m2o_fields(self, duplicate, using=None):
        """Overwrites original duplicate function.

        We dont clone m2o since our data model is a downward tree."""
        return duplicate
