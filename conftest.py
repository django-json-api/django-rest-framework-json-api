import os


def pytest_configure():
    from django.conf import settings
    try:
        from django import setup
    except ImportError:
        setup = lambda: None

    os.environ['DJANGO_SETTINGS_MODULE'] = 'example.settings'
    setup()
