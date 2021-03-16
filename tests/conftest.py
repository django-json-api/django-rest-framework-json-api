import pytest
from rest_framework.test import APIClient

from tests.models import (
    BasicModel,
    ForeignKeyTarget,
    ManyToManySource,
    ManyToManyTarget,
)


@pytest.fixture(autouse=True)
def use_rest_framework_json_api_defaults(settings):
    """
    Enfroce default settings for tests modules.


    As for now example and tests modules share the same settings file
    some defaults which have been overwritten in the example app need
    to be overwritten. This way testing actually happens on default resp.
    each test defines what non default setting it wants to test.

    Once migration to tests module is finished and tests can have
    its own settings file, this fixture can be removed.
    """

    settings.JSON_API_FORMAT_FIELD_NAMES = False
    settings.JSON_API_FORMAT_TYPES = False
    settings.JSON_API_PLURALIZE_TYPES = False


@pytest.fixture
def model(db):
    return BasicModel.objects.create(text="Model")


@pytest.fixture
def foreign_key_target(db):
    return ForeignKeyTarget.objects.create(name="Target")


@pytest.fixture
def many_to_many_source(db, many_to_many_targets):
    source = ManyToManySource.objects.create(name="Source")
    source.targets.add(*many_to_many_targets)
    return source


@pytest.fixture
def many_to_many_targets(db):
    return [
        ManyToManyTarget.objects.create(name="Target1"),
        ManyToManyTarget.objects.create(name="Target2"),
    ]


@pytest.fixture
def client():
    return APIClient()
