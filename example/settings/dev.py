import os

SITE_ID = 1
DEBUG = True

MEDIA_ROOT = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
MEDIA_URL = '/media/'

DATABASE_ENGINE = 'sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'drf_example',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.admin',
    'rest_framework',
    'example',
]

STATIC_URL = '/static/'

ROOT_URLCONF = 'example.urls'

SECRET_KEY = 'abc123'

PASSWORD_HASHERS = ('django.contrib.auth.hashers.UnsaltedMD5PasswordHasher', )

MIDDLEWARE_CLASSES = ()

JSON_API_FORMAT_KEYS = 'camelize'
JSON_API_FORMAT_RELATION_KEYS = 'camelize'
REST_FRAMEWORK = {
    'PAGE_SIZE': 5,
    'EXCEPTION_HANDLER': 'drf_search_categories.exceptions.exception_handler',
    'DEFAULT_PAGINATION_CLASS':
        'drf_search_categories.pagination.PageNumberPagination',
    'DEFAULT_PARSER_CLASSES': (
        'drf_search_categories.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'drf_search_categories.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_METADATA_CLASS': 'drf_search_categories.metadata.JSONAPIMetadata',
}
