from recipes.models import Tag
from rest_framework import viewsets

from . import serializers


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
