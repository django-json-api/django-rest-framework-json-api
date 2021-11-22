import os

SITE_ID = 1
DEBUG = True

MEDIA_ROOT = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
MEDIA_URL = "/media/"
USE_TZ = False

DATABASE_ENGINE = "sqlite3"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "drf_example",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sessions",
    "django.contrib.auth",
    "rest_framework_json_api",
    "rest_framework",
    "polymorphic",
    "example",
    "debug_toolbar",
    "django_filters",
    "tests",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # insert your TEMPLATE_DIRS here
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "/static/"

ROOT_URLCONF = "example.urls"

SECRET_KEY = "abc123"

PASSWORD_HASHERS = ("django.contrib.auth.hashers.UnsaltedMD5PasswordHasher",)

MIDDLEWARE = ("debug_toolbar.middleware.DebugToolbarMiddleware",)

INTERNAL_IPS = ("127.0.0.1",)

JSON_API_FORMAT_FIELD_NAMES = "camelize"
JSON_API_FORMAT_TYPES = "camelize"
REST_FRAMEWORK = {
    "PAGE_SIZE": 5,
    "EXCEPTION_HANDLER": "rest_framework_json_api.exceptions.exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework_json_api.pagination.JsonApiPageNumberPagination",
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework_json_api.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework_json_api.renderers.JSONRenderer",
        # If you're performance testing, you will want to use the browseable API
        # without forms, as the forms can generate their own queries.
        # If performance testing, enable:
        # 'example.utils.BrowsableAPIRendererWithoutForms',
        # Otherwise, to play around with the browseable API, enable:
        "rest_framework_json_api.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_METADATA_CLASS": "rest_framework_json_api.metadata.JSONAPIMetadata",
    "DEFAULT_SCHEMA_CLASS": "rest_framework_json_api.schemas.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework_json_api.filters.OrderingFilter",
        "rest_framework_json_api.django_filters.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ),
    "SEARCH_PARAM": "filter[search]",
    "TEST_REQUEST_RENDERER_CLASSES": (
        "rest_framework_json_api.renderers.JSONRenderer",
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "vnd.api+json",
}
