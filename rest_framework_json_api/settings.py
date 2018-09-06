"""
This module provides the `json_api_settings` object that is used to access
JSON API REST framework settings, checking for user settings first, then falling back to
the defaults.
"""

from django.conf import settings
from django.core.signals import setting_changed

JSON_API_SETTINGS_PREFIX = 'JSON_API_'

DEFAULTS = {
    'FORMAT_FIELD_NAMES': False,
    'FORMAT_TYPES': False,
    'PLURALIZE_TYPES': False,
    'UNIFORM_EXCEPTIONS': False,

    # deprecated settings to be removed in the future
    'FORMAT_KEYS': None,
    'FORMAT_RELATION_KEYS': None,
    'PLURALIZE_RELATION_TYPE': None,
}


class JSONAPISettings(object):
    """
    A settings object that allows json api settings to be access as
    properties.
    """

    def __init__(self, user_settings=settings, defaults=DEFAULTS):
        self.defaults = defaults
        self.user_settings = user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid JSON API setting: '%s'" % attr)

        value = getattr(self.user_settings, JSON_API_SETTINGS_PREFIX + attr, self.defaults[attr])

        # Cache the result
        setattr(self, attr, value)
        return value

    @property
    def format_type(self):
        if self.FORMAT_KEYS is not None:
            return self.FORMAT_KEYS

        return self.FORMAT_FIELD_NAMES


json_api_settings = JSONAPISettings()


def reload_json_api_settings(*args, **kwargs):
    django_setting = kwargs['setting']
    setting = django_setting.replace(JSON_API_SETTINGS_PREFIX, '')
    value = kwargs['value']
    if setting in DEFAULTS.keys():
        if value is not None:
            setattr(json_api_settings, setting, value)
        elif hasattr(json_api_settings, setting):
            delattr(json_api_settings, setting)


setting_changed.connect(reload_json_api_settings)
