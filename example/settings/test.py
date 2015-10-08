from .dev import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ROOT_URLCONF = 'example.urls_test'

JSON_API_FORMAT_KEYS = 'camelize'
JSON_API_FORMAT_RELATION_KEYS = 'camelize'
JSON_API_PLURALIZE_RELATION_TYPE = True
REST_FRAMEWORK.update({
    'PAGE_SIZE': 1,
})
