from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework import viewsets, decorators, response, mixins, status, exceptions

from recipes import models
from core import permissions, paginations

from . import serializers, filters

User = get_user_model()


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    pagination_class = paginations.CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return serializers.UserGetSerializer
        elif self.action in ('subscriptions', 'subscribe'):
            return serializers.SubscribeSerializer
        elif self.action in ('set_password',):
            return serializers.UsersChangePasswordSerializer
        return serializers.UsersCreateSerializer

    def retrieve(self, request, *args, **kwargs):
        if self.request.user == self.get_object():
            return redirect(reverse('users:users-me'))
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        password = serializer.validated_data.pop('password')
        user = serializer.save()
        user.set_password(password)
        user.save()

    @decorators.action(
        methods=['get'], detail=False, url_path='me', url_name='me',
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    @decorators.action(
        methods=['post'], detail=False, url_path='set_password', url_name='set_password',
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_set_password(serializer)
        headers = self.get_success_headers(serializer.data)
        return response.Response(status=status.HTTP_204_NO_CONTENT, headers=headers)

    def perform_set_password(self, serializer):
        instance = self.request.user
        curr_password = serializer.validated_data.get('current_password')
        if not instance.check_password(curr_password):
            raise exceptions.ValidationError('Неверный пароль!')
        new_password = serializer.validated_data.get('new_password')
        instance.set_password(new_password)
        instance.save()

    @decorators.action(
        methods=['get'], detail=False, url_path='subscriptions', url_name='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request, *args, **kwargs):
        instance = self.request.user
        subscriptions = instance.subscriber.all()
        subscribers = User.objects.filter(
            id__in=subscriptions.values('author'),
        )
        serializer = self.get_serializer(subscribers, many=True)
        return response.Response(serializer.data)

    def _create_subscribe(self, record):
        author = self.get_object()
        try:
            record.create(author=author)
        except IntegrityError:
            raise exceptions.ValidationError({'errors': 'Вы уже подписаны.'})
        serializer = self.get_serializer(author)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_subscribe(self, record):
        author = self.get_object()
        record = record.filter(author=author)
        if not record.exists():
            raise exceptions.ValidationError({'errors': 'Вы не были подписаны.'})
        record.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        methods=['post', 'delete'], detail=True, url_path='subscribe', url_name='subscribe',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        instance = self.request.user
        record = getattr(instance, 'subscriber')
        if self.request.method == 'POST':
            return self._create_subscribe(record)
        elif self.request.method == 'DELETE':
            return self._delete_subscribe(record)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagGetSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientGetSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = filters.IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    permission_classes = (permissions.IsOwnerOrAdminOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = filters.RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return serializers.RecipeGetSerializer
        elif self.action in ('favorite', 'shopping_cart'):
            return serializers.RecipeShortGetSerializer
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
