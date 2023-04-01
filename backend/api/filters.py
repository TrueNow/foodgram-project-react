from django.contrib.auth import get_user_model
from django_filters.rest_framework import filters, filterset, backends
from recipes.models import Ingredient, Recipe, Tag
from django.db import models

User = get_user_model()
DjangoFilterBackend = backends.DjangoFilterBackend


class IngredientFilter(filterset.FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filterset.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    author = filters.CharFilter(method='filter_author')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags',)

    def filter_author(self, queryset, name, value):
        if value.isdigit():
            return queryset.filter(**{name: value})
        if value == 'me':
            value = self.request.user.id
            return queryset.filter(**{name: value})
        return queryset

    def _filter_is_param(self, queryset, name, value, param):
        if value and self.request.user.is_authenticated:
            return queryset.filter(**{f'{param}__user': self.request.user})
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        return self._filter_is_param(queryset, name, value, param='favorite')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._filter_is_param(queryset, name, value, param='shopping_cart')
