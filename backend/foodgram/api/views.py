from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.utils import IntegrityError
from django.http import HttpResponse
from rest_framework import viewsets, decorators, response, status, exceptions
from rest_framework.decorators import action

from core import permissions
from recipes import models
from . import serializers, filters


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = filters.IngredientFilter


@action(detail=True)
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    permission_classes = (permissions.IsOwnerOrAdminOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = filters.RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeGetSerializer
        elif self.action in ('favorite', 'shopping_cart'):
            return serializers.ShortRecipeSerializer
        elif self.action in ('download_shopping_cart',):
            return serializers.ShoppingCartDownloadSerializer
        return serializers.RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _create_in_favorite_or_shopping_cart(self, record):
        recipe = self.get_object()
        try:
            record.create(recipe=recipe)
        except IntegrityError:
            raise exceptions.ValidationError({'errors': 'Рецепт уже добавлен!'})
        serializer = self.get_serializer(recipe)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_in_favorite_or_shopping_cart(self, record):
        recipe = self.get_object()
        record = record.filter(recipe=recipe)
        if not record.exists():
            raise exceptions.ValidationError({'errors': 'Рецепта не найдено.'})
        record.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def _favorite_or_shopping_cart_view(self):
        instance = self.request.user
        record = getattr(instance, self.action)
        if self.request.method == 'POST':
            return self._create_in_favorite_or_shopping_cart(record)
        if self.request.method == 'DELETE':
            return self._delete_in_favorite_or_shopping_cart(record)

    @decorators.action(
        methods=['delete', 'post'], detail=True, url_path='favorite', url_name='favorite',
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, *args, **kwargs):
        return self._favorite_or_shopping_cart_view()

    @decorators.action(
        methods=['delete', 'post'], detail=True, url_path='shopping_cart', url_name='shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, *args, **kwargs):
        return self._favorite_or_shopping_cart_view()

    @decorators.action(
        methods=['get'], detail=False,
        url_path='download_shopping_cart', url_name='download_shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        user = request.user
        if not user.shopping_cart.exists():
            return response.Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = models.IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        today = datetime.today()
        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
            f'Дата: {today:%Y-%m-%d}\n\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        resp = HttpResponse(shopping_list, content_type='text/plain')
        resp['Content-Disposition'] = f'attachment; filename={filename}'
        return resp
