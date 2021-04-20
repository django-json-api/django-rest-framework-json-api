# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots[
    "test_path_without_parameters 1"
] = """{
  "description": "",
  "operationId": "List/authors/",
  "parameters": [
    {
      "$ref": "#/components/parameters/include"
    },
    {
      "$ref": "#/components/parameters/fields"
    },
    {
      "$ref": "#/components/parameters/sort"
    },
    {
      "description": "A page number within the paginated result set.",
      "in": "query",
      "name": "page[number]",
      "required": false,
      "schema": {
        "type": "integer"
      }
    },
    {
      "description": "Number of results to return per page.",
      "in": "query",
      "name": "page[size]",
      "required": false,
      "schema": {
        "type": "integer"
      }
    },
    {
      "description": "Which field to use when ordering the results.",
      "in": "query",
      "name": "sort",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "description": "A search term.",
      "in": "query",
      "name": "filter[search]",
      "required": false,
      "schema": {
        "type": "string"
      }
    }
  ],
  "responses": {
    "200": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "properties": {
              "data": {
                "items": {
                  "$ref": "#/components/schemas/AuthorList"
                },
                "type": "array"
              },
              "included": {
                "items": {
                  "$ref": "#/components/schemas/resource"
                },
                "type": "array",
                "uniqueItems": true
              },
              "jsonapi": {
                "$ref": "#/components/schemas/jsonapi"
              },
              "links": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/links"
                  },
                  {
                    "$ref": "#/components/schemas/pagination"
                  }
                ],
                "description": "Link members related to primary data"
              }
            },
            "required": [
              "data"
            ],
            "type": "object"
          }
        }
      },
      "description": "List/authors/"
    },
    "401": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "not authorized"
    },
    "404": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "not found"
    }
  },
  "tags": [
    "authors"
  ]
}"""

snapshots[
    "test_path_with_id_parameter 1"
] = """{
  "description": "",
  "operationId": "retrieve/authors/{id}/",
  "parameters": [
    {
      "description": "A unique integer value identifying this author.",
      "in": "path",
      "name": "id",
      "required": true,
      "schema": {
        "type": "string"
      }
    },
    {
      "$ref": "#/components/parameters/include"
    },
    {
      "$ref": "#/components/parameters/fields"
    },
    {
      "$ref": "#/components/parameters/sort"
    },
    {
      "description": "Which field to use when ordering the results.",
      "in": "query",
      "name": "sort",
      "required": false,
      "schema": {
        "type": "string"
      }
    },
    {
      "description": "A search term.",
      "in": "query",
      "name": "filter[search]",
      "required": false,
      "schema": {
        "type": "string"
      }
    }
  ],
  "responses": {
    "200": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "properties": {
              "data": {
                "$ref": "#/components/schemas/AuthorDetail"
              },
              "included": {
                "items": {
                  "$ref": "#/components/schemas/resource"
                },
                "type": "array",
                "uniqueItems": true
              },
              "jsonapi": {
                "$ref": "#/components/schemas/jsonapi"
              },
              "links": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/links"
                  },
                  {
                    "$ref": "#/components/schemas/pagination"
                  }
                ],
                "description": "Link members related to primary data"
              }
            },
            "required": [
              "data"
            ],
            "type": "object"
          }
        }
      },
      "description": "retrieve/authors/{id}/"
    },
    "401": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "not authorized"
    },
    "404": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "not found"
    }
  },
  "tags": [
    "authors"
  ]
}"""

snapshots[
    "test_post_request 1"
] = """{
  "description": "",
  "operationId": "create/authors/",
  "parameters": [],
  "requestBody": {
    "content": {
      "application/vnd.api+json": {
        "schema": {
          "properties": {
            "data": {
              "additionalProperties": false,
              "properties": {
                "attributes": {
                  "properties": {
                    "defaults": {
                      "default": "default",
                      "description": "help for defaults",
                      "maxLength": 20,
                      "minLength": 3,
                      "type": "string",
                      "writeOnly": true
                    },
                    "email": {
                      "format": "email",
                      "maxLength": 254,
                      "type": "string"
                    },
                    "name": {
                      "maxLength": 50,
                      "type": "string"
                    }
                  },
                  "required": [
                    "name",
                    "email"
                  ],
                  "type": "object"
                },
                "id": {
                  "$ref": "#/components/schemas/id"
                },
                "links": {
                  "properties": {
                    "self": {
                      "$ref": "#/components/schemas/link"
                    }
                  },
                  "type": "object"
                },
                "relationships": {
                  "properties": {
                    "bio": {
                      "$ref": "#/components/schemas/reltoone"
                    },
                    "comments": {
                      "$ref": "#/components/schemas/reltomany"
                    },
                    "entries": {
                      "$ref": "#/components/schemas/reltomany"
                    },
                    "first_entry": {
                      "$ref": "#/components/schemas/reltoone"
                    },
                    "type": {
                      "$ref": "#/components/schemas/reltoone"
                    }
                  },
                  "type": "object"
                },
                "type": {
                  "$ref": "#/components/schemas/type"
                }
              },
              "required": [
                "type"
              ],
              "type": "object"
            }
          },
          "required": [
            "data"
          ]
        }
      }
    }
  },
  "responses": {
    "201": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "properties": {
              "data": {
                "$ref": "#/components/schemas/Author"
              },
              "included": {
                "items": {
                  "$ref": "#/components/schemas/resource"
                },
                "type": "array",
                "uniqueItems": true
              },
              "jsonapi": {
                "$ref": "#/components/schemas/jsonapi"
              },
              "links": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/links"
                  },
                  {
                    "$ref": "#/components/schemas/pagination"
                  }
                ],
                "description": "Link members related to primary data"
              }
            },
            "required": [
              "data"
            ],
            "type": "object"
          }
        }
      },
      "description": "[Created](https://jsonapi.org/format/#crud-creating-responses-201). Assigned `id` and/or any other changes are in this response."
    },
    "202": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/datum"
          }
        }
      },
      "description": "Accepted for [asynchronous processing](https://jsonapi.org/recommendations/#asynchronous-processing)"
    },
    "204": {
      "description": "[Created](https://jsonapi.org/format/#crud-creating-responses-204) with the supplied `id`. No other changes from what was POSTed."
    },
    "401": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "not authorized"
    },
    "403": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "[Forbidden](https://jsonapi.org/format/#crud-creating-responses-403)"
    },
    "404": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "[Related resource does not exist](https://jsonapi.org/format/#crud-creating-responses-404)"
    },
    "409": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "[Conflict](https://jsonapi.org/format/#crud-creating-responses-409)"
    }
  },
  "tags": [
    "authors"
  ]
}"""

snapshots[
    "test_patch_request 1"
] = """{
  "description": "",
  "operationId": "update/authors/{id}",
  "parameters": [
    {
      "description": "A unique integer value identifying this author.",
      "in": "path",
      "name": "id",
      "required": true,
      "schema": {
        "type": "string"
      }
    }
  ],
  "requestBody": {
    "content": {
      "application/vnd.api+json": {
        "schema": {
          "properties": {
            "data": {
              "additionalProperties": false,
              "properties": {
                "attributes": {
                  "properties": {
                    "defaults": {
                      "default": "default",
                      "description": "help for defaults",
                      "maxLength": 20,
                      "minLength": 3,
                      "type": "string",
                      "writeOnly": true
                    },
                    "email": {
                      "format": "email",
                      "maxLength": 254,
                      "type": "string"
                    },
                    "name": {
                      "maxLength": 50,
                      "type": "string"
                    }
                  },
                  "type": "object"
                },
                "id": {
                  "$ref": "#/components/schemas/id"
                },
                "links": {
                  "properties": {
                    "self": {
                      "$ref": "#/components/schemas/link"
                    }
                  },
                  "type": "object"
                },
                "relationships": {
                  "properties": {
                    "bio": {
                      "$ref": "#/components/schemas/reltoone"
                    },
                    "comments": {
                      "$ref": "#/components/schemas/reltomany"
                    },
                    "entries": {
                      "$ref": "#/components/schemas/reltomany"
                    },
                    "first_entry": {
                      "$ref": "#/components/schemas/reltoone"
                    },
                    "type": {
                      "$ref": "#/components/schemas/reltoone"
                    }
                  },
                  "type": "object"
                },
                "type": {
                  "$ref": "#/components/schemas/type"
                }
              },
              "required": [
                "type",
                "id"
              ],
              "type": "object"
            }
          },
          "required": [
            "data"
          ]
        }
      }
    }
  },
  "responses": {
    "200": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "properties": {
              "data": {
                "$ref": "#/components/schemas/Author"
              },
              "included": {
                "items": {
                  "$ref": "#/components/schemas/resource"
                },
                "type": "array",
                "uniqueItems": true
              },
              "jsonapi": {
                "$ref": "#/components/schemas/jsonapi"
              },
              "links": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/links"
                  },
                  {
                    "$ref": "#/components/schemas/pagination"
                  }
                ],
                "description": "Link members related to primary data"
              }
            },
            "required": [
              "data"
            ],
            "type": "object"
          }
        }
      },
      "description": "update/authors/{id}"
    },
    "401": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "not authorized"
    },
    "403": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "[Forbidden](https://jsonapi.org/format/#crud-updating-responses-403)"
    },
    "404": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "[Related resource does not exist](https://jsonapi.org/format/#crud-updating-responses-404)"
    },
    "409": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "[Conflict]([Conflict](https://jsonapi.org/format/#crud-updating-responses-409)"
    }
  },
  "tags": [
    "authors"
  ]
}"""

snapshots[
    "test_delete_request 1"
] = """{
  "description": "",
  "operationId": "destroy/authors/{id}",
  "parameters": [
    {
      "description": "A unique integer value identifying this author.",
      "in": "path",
      "name": "id",
      "required": true,
      "schema": {
        "type": "string"
      }
    }
  ],
  "responses": {
    "200": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/onlymeta"
          }
        }
      },
      "description": "[OK](https://jsonapi.org/format/#crud-deleting-responses-200)"
    },
    "202": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/datum"
          }
        }
      },
      "description": "Accepted for [asynchronous processing](https://jsonapi.org/recommendations/#asynchronous-processing)"
    },
    "204": {
      "description": "[no content](https://jsonapi.org/format/#crud-deleting-responses-204)"
    },
    "401": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "not authorized"
    },
    "404": {
      "content": {
        "application/vnd.api+json": {
          "schema": {
            "$ref": "#/components/schemas/failure"
          }
        }
      },
      "description": "[Resource does not exist](https://jsonapi.org/format/#crud-deleting-responses-404)"
    }
  },
  "tags": [
    "authors"
  ]
}"""
