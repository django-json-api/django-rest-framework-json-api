import pytest

from rest_framework_json_api.settings import json_api_settings


def test_settings_invalid():
    with pytest.raises(AttributeError):
        json_api_settings.INVALID_SETTING


def test_settings_default():
    assert json_api_settings.UNIFORM_EXCEPTIONS is False


def test_settings_override(settings):
    settings.JSON_API_FORMAT_FIELD_NAMES = 'dasherize'
    assert json_api_settings.FORMAT_FIELD_NAMES == 'dasherize'
