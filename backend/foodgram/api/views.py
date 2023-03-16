from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, IngredientAmount
from rest_framework import viewsets, decorators, response, status

from . import serializers


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientAmountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IngredientAmount.objects.all()
    serializer_class = serializers.IngredientAmountSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeGetSerializer
        elif self.action in ('favorite', 'shopping_cart'):
            return serializers.RecipeCreateSerializer
        elif self.action in ('download_shopping_cart',):
            return serializers.ShoppingCartDownloadSerializer

    def favorite_shopping_view(self, related_name):
        instance = self.request.user
        recipe = self.get_object()
        queryset = getattr(instance, related_name).filter(recipe=recipe)
        if self.request.method == 'POST':
            if queryset.exists():
                return response.Response(
                    data={'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            getattr(instance, related_name).create(recipe=recipe)
            serializer = serializers.ShortRecipeSerializer(recipe)
            return response.Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            if queryset.exists():
                queryset.delete()
                return response.Response(status=status.HTTP_204_NO_CONTENT)
            return response.Response(
                data={'errors': 'Невозможно удалить, рецепт не добавлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @decorators.action(methods=['delete', 'post'], detail=True, url_path='favorite', url_name='favorite')
    def favorite(self, request, pk=None, **kwargs):
        return self.favorite_shopping_view('favorite')

    @decorators.action(methods=['delete', 'post'], detail=True, url_path='shopping_cart', url_name='shopping_cart')
    def shopping_cart(self, request, pk=None, **kwargs):
        return self.favorite_shopping_view('shopping_cart')

    @decorators.action(
        methods=['get'], detail=False,
        url_path='download_shopping_cart', url_name='download_shopping_cart'
    )
    def download_shopping_cart(self, request, **kwargs):
        instance = self.request.user
        shopping_cart = instance.shopping_cart.all()
        recipes = Recipe.objects.filter(
            id__in=shopping_cart.values('recipe')
        )
        serializer = self.get_serializer(recipes, many=True)
        return response.Response(serializer.data)
