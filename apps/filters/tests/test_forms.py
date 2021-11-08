import pytest
from apps.base.tests.asserts import assertFormChoicesLength
from apps.base.tests.mock_data import TABLE
from apps.filters.forms import FilterForm
from django.http import QueryDict

pytestmark = pytest.mark.django_db


def test_filter_form(filter_factory, node_factory):
    filter_ = filter_factory(node=node_factory())
    form = FilterForm(instance=filter_, schema=TABLE.schema())

    assert set(form.fields.keys()) == {"hidden_live", "column"}
    assertFormChoicesLength(form, "column", 9)

    data = QueryDict(mutable=True)
    data["column"] = "id"
    form = FilterForm(instance=filter_, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"hidden_live", "column", "numeric_predicate"}
    assertFormChoicesLength(form, "numeric_predicate", 11)

    data["numeric_predicate"] = "isnull"
    form = FilterForm(instance=filter_, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {"hidden_live", "column", "numeric_predicate"}

    data["numeric_predicate"] = "equal"
    form = FilterForm(instance=filter_, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {
        "hidden_live",
        "column",
        "numeric_predicate",
        "integer_value",
    }

    data["numeric_predicate"] = "isin"
    form = FilterForm(instance=filter_, schema=TABLE.schema(), data=data)
    assert set(form.fields.keys()) == {
        "hidden_live",
        "column",
        "numeric_predicate",
        "integer_values",
    }
