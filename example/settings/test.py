from .dev import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "example.urls_test"

JSON_API_FORMAT_FIELD_NAMES = "camelize"
JSON_API_FORMAT_TYPES = "camelize"
JSON_API_PLURALIZE_TYPES = True

REST_FRAMEWORK.update(  # noqa: F405
    {  # noqa
        "PAGE_SIZE": 1,
    }
)
