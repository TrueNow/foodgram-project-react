from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, IngredientAmount
from rest_framework import viewsets, decorators, response, status, exceptions, filters
from . import serializers, permissions


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (permissions.RecipePermission,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeGetSerializer
        elif self.action in ('favorite', 'shopping_cart'):
            return serializers.ShortRecipeSerializer
        elif self.action in ('download_shopping_cart',):
            return serializers.ShoppingCartDownloadSerializer
        return serializers.RecipeCreateSerializer

    def _create_in_favorite(self, record):
        recipe = self.get_object()
        try:
            record.create(recipe=recipe)
        except IntegrityError:
            raise exceptions.ValidationError({'errors': 'Рецепт уже добавлен!'})
        serializer = self.get_serializer(recipe)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_in_favorite(self, record):
        recipe = self.get_object()
        record = record.filter(recipe=recipe)
        if not record.exists():
            raise exceptions.ValidationError({'errors': 'Рецепта не найдено.'})
        record.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def _favorite_view(self):
        instance = self.request.user
        record = getattr(instance, self.action)
        if self.request.method == 'POST':
            return self._create_in_favorite(record)
        if self.request.method == 'DELETE':
            return self._delete_in_favorite(record)

    @decorators.action(methods=['delete', 'post'], detail=True, url_path='favorite', url_name='favorite')
    def favorite(self, request, *args, **kwargs):
        return self._favorite_view()

    @decorators.action(methods=['delete', 'post'], detail=True, url_path='shopping_cart', url_name='shopping_cart')
    def shopping_cart(self, request, *args, **kwargs):
        return self._favorite_view()

    @decorators.action(
        methods=['get'], detail=False,
        url_path='download_shopping_cart', url_name='download_shopping_cart'
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        instance = self.request.user
        shopping_cart = instance.shopping_cart.all()
        recipes = Recipe.objects.filter(
            id__in=shopping_cart.values('recipe')
        )
        serializer = self.get_serializer(recipes, many=True)
        return response.Response(serializer.data)
