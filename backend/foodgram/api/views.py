from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, IngredientAmount
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


class IngredientAmountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IngredientAmount.objects.all()
    serializer_class = serializers.IngredientAmountSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    lookup_field = 'recipe_pk'

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer
        return serializers.RecipeWriteSerializer

    @decorators.action(methods=['delete', 'post'], detail=True, url_path='favorite', url_name='favorite')
    def favorite(self, request, pk=None, **kwargs):
        instance = self.request.user
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('recipe_pk'))
        favorite = Favorite.objects.filter(recipe=recipe.pk, user=instance)
        if self.request.method == 'POST':
            if favorite.exists():
                return response.Response(
                    data={'errors': 'Рецепт уже в избранном!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(recipe=recipe, user=instance)
            serializer = serializers.RecipeAuthorSerializer(recipe)
            return response.Response(serializer.data, status=status.HTTP_201_CREATED)

        if favorite.exists():
            favorite.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(
            data={'errors': 'Невозможно удалить! Рецепт не был в избранном.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @decorators.action(methods=['delete', 'post'], detail=True, url_path='shopping_cart', url_name='shopping_cart')
    def shopping_cart(self, request, pk=None, **kwargs):
        instance = self.request.user
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('recipe_pk'))
        shopping_cart = ShoppingCart.objects.filter(recipe=recipe.pk, user=instance)
        if self.request.method == 'POST':
            if shopping_cart.exists():
                return response.Response(
                    data={'errors': 'Рецепт уже в списке покупок!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(recipe=recipe, user=instance)
            serializer = serializers.RecipeAuthorSerializer(recipe)
            return response.Response(serializer.data, status=status.HTTP_201_CREATED)

        if shopping_cart.exists():
            shopping_cart.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(
            data={'errors': 'Невозможно удалить! Рецепт не был добавлен в список покупок.'},
            status=status.HTTP_400_BAD_REQUEST
        )
