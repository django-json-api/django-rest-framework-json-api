from .dev import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ROOT_URLCONF = 'example.urls_test'

JSON_API_FIELD_NAMES = 'camelize'
JSON_API_FORMAT_TYPES = 'camelize'
JSON_API_PLURALIZE_TYPES = True
# TODO: 13 tests fail when this is True because they use `page` and `page_size`. Fix them.
JSON_API_STANDARD_PAGINATION = False

REST_FRAMEWORK.update({
    'PAGE_SIZE': 1,
})
