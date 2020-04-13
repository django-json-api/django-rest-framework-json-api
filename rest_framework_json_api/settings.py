"""
This module provides the `json_api_settings` object that is used to access
JSON API REST framework settings, checking for user settings first, then falling back to
the defaults.
"""

from django.conf import settings
from django.core.signals import setting_changed
import warnings

JSON_API_SETTINGS_PREFIX = 'JSON_API_'

DEFAULTS = {
    'FORMAT_FIELD_NAMES': False,
    'FORMAT_TYPES': False,
    'PLURALIZE_TYPES': False,
    'UNIFORM_EXCEPTIONS': False,
    'SERIALIZE_NESTED_SERIALIZERS_AS_ATTRIBUTE': False
}


class JSONAPISettings(object):
    """
    A settings object that allows json api settings to be access as
    properties.
    """

    def __init__(self, user_settings=settings, defaults=DEFAULTS):
        self.defaults = defaults
        self.user_settings = user_settings

        field_name = JSON_API_SETTINGS_PREFIX + 'SERIALIZE_NESTED_SERIALIZERS_AS_ATTRIBUTE'

        value = getattr(
            self.user_settings,
            field_name,
            self.defaults['SERIALIZE_NESTED_SERIALIZERS_AS_ATTRIBUTE'])

        if not value and not hasattr(self.user_settings, field_name):
            warnings.warn(DeprecationWarning(
                "Rendering nested serializers in relations by default is deprecated and will be "
                "changed in future releases. Please, use ResourceRelatedField or set "
                "JSON_API_SERIALIZE_NESTED_SERIALIZERS_AS_ATTRIBUTE to False"))

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid JSON API setting: '%s'" % attr)

        value = getattr(self.user_settings, JSON_API_SETTINGS_PREFIX + attr, self.defaults[attr])

        # Cache the result
        setattr(self, attr, value)
        return value


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
