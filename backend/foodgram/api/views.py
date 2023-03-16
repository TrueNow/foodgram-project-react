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
    lookup_field = 'recipe_pk'

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeReadSerializer
        elif self.action in ('download_shopping_cart',):
            return serializers.ShoppingCartSerializer
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
