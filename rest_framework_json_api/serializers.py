from rest_framework.serializers import HyperlinkedModelSerializer

from rest_framework_json_api.relations import JSONAPIRelatedField


class JSONAPIModelSerializer(HyperlinkedModelSerializer):
    """
    A type of `ModelSerializer` that uses hyperlinked relationships instead
    of primary key relationships. Specifically:

    * A 'url' field is included instead of the 'id' field.
    * Relationships to other instances are hyperlinks, instead of primary keys.
    * Uses django-rest-framework-json-api JSONAPIRelatedField instead of the default HyperlinkedRelatedField
    """
    serializer_related_field = JSONAPIRelatedField
