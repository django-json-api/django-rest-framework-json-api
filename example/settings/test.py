from .dev import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ROOT_URLCONF = 'example.urls_test'

JSON_API_FORMAT_KEYS = 'camelize'
JSON_API_FORMAT_TYPES = 'camelize'
JSON_API_PLURALIZE_TYPES = True
REST_FRAMEWORK.update({
    'PAGE_SIZE': 1,
})
JSON_API_POLYMORPHIC_ANCESTORS = (
    'polymorphic.models.PolymorphicModel',
)
