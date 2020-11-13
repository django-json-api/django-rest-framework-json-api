# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_first_level_attribute_error 1"] = {
    "errors": [
        {
            "code": "required",
            "detail": "This field is required.",
            "source": {"pointer": "/data/attributes/headline"},
            "status": "400",
        }
    ]
}

snapshots["test_first_level_custom_attribute_error 1"] = {
    "errors": [
        {
            "detail": "Too short",
            "source": {"pointer": "/data/attributes/body-text"},
            "title": "Too Short title",
        }
    ]
}

snapshots["test_many_third_level_dict_errors 1"] = {
    "errors": [
        {
            "code": "required",
            "detail": "This field is required.",
            "source": {"pointer": "/data/attributes/comments/0/attachment/data"},
            "status": "400",
        },
        {
            "code": "required",
            "detail": "This field is required.",
            "source": {"pointer": "/data/attributes/comments/0/body"},
            "status": "400",
        },
    ]
}

snapshots["test_second_level_array_error 1"] = {
    "errors": [
        {
            "code": "required",
            "detail": "This field is required.",
            "source": {"pointer": "/data/attributes/comments/0/body"},
            "status": "400",
        }
    ]
}

snapshots["test_second_level_dict_error 1"] = {
    "errors": [
        {
            "code": "required",
            "detail": "This field is required.",
            "source": {"pointer": "/data/attributes/comment/body"},
            "status": "400",
        }
    ]
}

snapshots["test_third_level_array_error 1"] = {
    "errors": [
        {
            "code": "required",
            "detail": "This field is required.",
            "source": {"pointer": "/data/attributes/comments/0/attachments/0/data"},
            "status": "400",
        }
    ]
}

snapshots["test_third_level_custom_array_error 1"] = {
    "errors": [
        {
            "code": "invalid",
            "detail": "Too short data",
            "source": {"pointer": "/data/attributes/comments/0/attachments/0/data"},
            "status": "400",
        }
    ]
}

snapshots["test_third_level_dict_error 1"] = {
    "errors": [
        {
            "code": "required",
            "detail": "This field is required.",
            "source": {"pointer": "/data/attributes/comments/0/attachment/data"},
            "status": "400",
        }
    ]
}
