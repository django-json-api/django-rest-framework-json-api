from rest_framework.serializers import *

from rest_framework_json_api.relations import HyperlinkedRelatedField


class HyperlinkedModelSerializer(HyperlinkedModelSerializer):
    """
    A type of `ModelSerializer` that uses hyperlinked relationships instead
    of primary key relationships. Specifically:

    * A 'url' field is included instead of the 'id' field.
    * Relationships to other instances are hyperlinks, instead of primary keys.
    * Uses django-rest-framework-json-api HyperlinkedRelatedField instead of the default HyperlinkedRelatedField
    """
    serializer_related_field = HyperlinkedRelatedField
