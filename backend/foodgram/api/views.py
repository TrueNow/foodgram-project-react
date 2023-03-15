from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from recipes.models import Tag, Ingredient, Recipe
from users.models import Subscription
from rest_framework import viewsets, decorators, response, mixins, status

from . import serializers


User = get_user_model()


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    lookup_field = 'user_pk'

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return serializers.UserReadSerializer
        return serializers.UserWriteSerializer

    @decorators.action(methods=['get'], detail=False, url_path='me', url_name='me')
    def me(self, request):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    @decorators.action(methods=['delete', 'post'], detail=True, url_path='subscribe', url_name='subscribe')
    def subscribe(self, request, pk=None, **kwargs):
        instance = self.request.user
        author = get_object_or_404(User, pk=self.kwargs.get('user_pk'))
        subscription = Subscription.objects.filter(author=author, subscriber=instance)
        if self.request.method == 'POST':
            if subscription.exists():
                return response.Response('Уже есть!', status=status.HTTP_400_BAD_REQUEST)
            subscription = Subscription.objects.create(author=author, subscriber=instance)
            serializer = serializers.SubscribeSerializer(subscription)
            return response.Response(serializer.data)

        if subscription.exists():
            subscription.delete()
            return response.Response('Удалил')
        return response.Response('такого не существует! не могу удалить!')


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer
        return serializers.RecipeWriteSerializer
