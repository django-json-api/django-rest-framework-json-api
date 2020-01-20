
# Getting Started

*Note: this package is named Django REST Framework JSON API to follow the naming
convention of other Django REST Framework packages. Since that's quite a bit
to say or type this package will be referred to as DJA elsewhere in these docs.*

By default, Django REST Framework produces a response like:
``` js
{
    "count": 20,
    "next": "http://example.com/api/1.0/identities/?page=3",
    "previous": "http://example.com/api/1.0/identities/?page=1",
    "results": [{
        "id": 3,
        "username": "john",
        "full_name": "John Coltrane"
    }]
}
```


However, for the same `identity` model in JSON API format the response should look
like the following:
``` js
{
    "links": {
        "first": "http://example.com/api/1.0/identities",
        "last": "http://example.com/api/1.0/identities?page=5",
        "next": "http://example.com/api/1.0/identities?page=3",
        "prev": "http://example.com/api/1.0/identities",
    },
    "data": [{
        "type": "identities",
        "id": 3,
        "attributes": {
            "username": "john",
            "full-name": "John Coltrane"
        }
    }],
    "meta": {
        "pagination": {
          "page": "2",
          "pages": "5",
          "count": "20"
        }
    }
}
```


## Requirements

1. Python (3.5, 3.6, 3.7, 3.8)
2. Django (1.11, 2.1, 2.2, 3.0)
3. Django REST Framework (3.10, 3.11)

We **highly** recommend and only officially support the latest patch release of each Python, Django and REST Framework series.

## Installation

From PyPI

    pip install djangorestframework-jsonapi
    # for optional package integrations
    pip install djangorestframework-jsonapi['django-filter']
    pip install djangorestframework-jsonapi['django-polymorphic']

From Source

    git clone https://github.com/django-json-api/django-rest-framework-json-api.git
    cd django-rest-framework-json-api && pip install -e .

## Running the example app

	git clone https://github.com/django-json-api/django-rest-framework-json-api.git
	cd django-rest-framework-json-api
	python3 -m venv env
	source env/bin/activate
	pip install -U -e . r requirements.txt
	django-admin migrate --settings=example.settings
	django-admin loaddata drf_example --settings=example.settings
	django-admin runserver --settings=example.settings


Browse to http://localhost:8000

## Running Tests

    pip install tox
    tox

