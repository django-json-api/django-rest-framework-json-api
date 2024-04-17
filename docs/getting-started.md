
# Getting Started

*Note: this package is named Django REST framework JSON:API to follow the naming
convention of other Django REST framework packages. Since that's quite a bit
to say or type this package will be referred to as DJA elsewhere in these docs.*

By default, Django REST framework produces a response like:
``` js
{
    "count": 20,
    "next": "https://example.com/api/1.0/identities/?page=3",
    "previous": "https://example.com/api/1.0/identities/?page=1",
    "results": [{
        "id": 3,
        "username": "john",
        "full_name": "John Coltrane"
    }]
}
```


However, for the same `identity` model in JSON:API format the response should look
like the following:
``` js
{
    "links": {
        "first": "https://example.com/api/1.0/identities",
        "last": "https://example.com/api/1.0/identities?page=5",
        "next": "https://example.com/api/1.0/identities?page=3",
        "prev": "https://example.com/api/1.0/identities",
    },
    "data": [{
        "type": "identities",
        "id": "3",
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

1. Python (3.8, 3.9, 3.10, 3.11, 3.12)
2. Django (4.2, 5.0)
3. Django REST framework (3.14, 3.15)

We **highly** recommend and only officially support the latest patch release of each Python, Django and REST framework series.

Generally Python and Django series are supported till the official end of life. For Django REST framework the last two series are supported.

For optional dependencies such as Django Filter only the latest release is officially supported even though lower versions should work as well.

## Installation

Install using `pip`...

    pip install djangorestframework-jsonapi
    # for optional package integrations
    pip install djangorestframework-jsonapi['django-filter']
    pip install djangorestframework-jsonapi['django-polymorphic']
    pip install djangorestframework-jsonapi['openapi']

or from source...

    git clone https://github.com/django-json-api/django-rest-framework-json-api.git
    cd django-rest-framework-json-api && pip install -e .


and add `rest_framework_json_api` to your `INSTALLED_APPS` setting below `rest_framework`.

    INSTALLED_APPS = [
        ...
        'rest_framework',
        'rest_framework_json_api',
        ...
    ]

## Running the example app

	git clone https://github.com/django-json-api/django-rest-framework-json-api.git
	cd django-rest-framework-json-api
	python3 -m venv env
	source env/bin/activate
	pip install -Ur requirements.txt
	django-admin migrate --settings=example.settings
	django-admin loaddata drf_example --settings=example.settings
	django-admin runserver --settings=example.settings


Browse to
* [http://localhost:8000](http://localhost:8000) for the list of available collections (in a non-JSON:API format!),
* [http://localhost:8000/swagger-ui/](http://localhost:8000/swagger-ui/) for a Swagger user interface to the dynamic schema view, or
* [http://localhost:8000/openapi](http://localhost:8000/openapi) for the schema view's OpenAPI specification document.

## Running Tests

    pip install tox
    tox

