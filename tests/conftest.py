import pytest
from rest_framework.test import APIClient

from tests.models import (
    BasicModel,
    ForeignKeySource,
    ForeignKeyTarget,
    ManyToManySource,
    ManyToManyTarget,
    NestedRelatedSource,
    URLModel,
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
def url_instance(db):
    return URLModel.objects.create(text="Url", url="https://example.com")


@pytest.fixture
def foreign_key_target(db):
    return ForeignKeyTarget.objects.create(name="Target")


@pytest.fixture
def foreign_key_source(db, foreign_key_target):
    return ForeignKeySource.objects.create(name="Source", target=foreign_key_target)


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
def many_to_many_sources(db, many_to_many_targets):
    source1 = ManyToManySource.objects.create(name="Source1")
    source2 = ManyToManySource.objects.create(name="Source2")

    source1.targets.add(*many_to_many_targets)
    source2.targets.add(*many_to_many_targets)

    return [source1, source2]


@pytest.fixture
def nested_related_source(
    db,
    foreign_key_source,
    foreign_key_target,
    many_to_many_targets,
    many_to_many_sources,
):
    source = NestedRelatedSource.objects.create(
        fk_source=foreign_key_source, fk_target=foreign_key_target
    )
    source.m2m_targets.add(*many_to_many_targets)
    source.m2m_sources.add(*many_to_many_sources)

    return source


@pytest.fixture
def client():
    return APIClient()
