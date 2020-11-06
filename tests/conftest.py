import pytest


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
