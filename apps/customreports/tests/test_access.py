import pytest 
pytestmark = pytest.mark.django_db

def test_access(client, user):
  assert False