import pytest


@pytest.fixture(autouse=True)
def patches(mocker, settings):
    # use filesystem instead of google cloud storage
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

    yield
