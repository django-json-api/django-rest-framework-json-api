"""
This module provides the `json_api_settings` object that is used to access
Django REST framework JSON:API settings, checking for user settings first, then falling back to
the defaults.
"""

from django.conf import settings
from django.core.signals import setting_changed

JSON_API_SETTINGS_PREFIX = "JSON_API_"

DEFAULTS = {
    "FORMAT_FIELD_NAMES": False,
    "FORMAT_TYPES": False,
    "FORMAT_RELATED_LINKS": False,
    "PLURALIZE_TYPES": False,
    "UNIFORM_EXCEPTIONS": False,
}


class JSONAPISettings:
    """
    A settings object that allows JSON:API settings to be access as
    properties.
    """

    def __init__(self, user_settings=settings, defaults=DEFAULTS):
        self.defaults = defaults
        self.user_settings = user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError(f"Invalid JSON:API setting: '{attr}'")

        value = getattr(
            self.user_settings, JSON_API_SETTINGS_PREFIX + attr, self.defaults[attr]
        )

        # Cache the result
        setattr(self, attr, value)
        return value


json_api_settings = JSONAPISettings()


def reload_json_api_settings(*args, **kwargs):
    django_setting = kwargs["setting"]
    setting = django_setting.replace(JSON_API_SETTINGS_PREFIX, "")
    value = kwargs["value"]
    if setting in DEFAULTS.keys():
        if value is not None:
            setattr(json_api_settings, setting, value)
        elif hasattr(json_api_settings, setting):
            delattr(json_api_settings, setting)


setting_changed.connect(reload_json_api_settings)
