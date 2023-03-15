from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.models import Tag, Ingredient, Recipe, IngredientAmount
from users.models import Subscription


User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            # 'is_subscribed'
        )


class UserWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientAmountSerializer(many=True, read_only=True)
    author = UserReadSerializer()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags',
            # 'is_favorited', 'is_in_shopping_cart',
            'author', 'name', 'image', 'text', 'cooking_time'
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = serializers.SlugRelatedField(
        slug_field='id', many=True, queryset=Ingredient.objects.all()
    )
    tags = serializers.SlugRelatedField(
        slug_field='id', many=True, queryset=Tag.objects.all()
    )
    author = serializers.SlugRelatedField(
        slug_field='id', queryset=User.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients',
            # 'is_favorited', 'is_in_shopping_cart',
            'author', 'name', 'image', 'text', 'cooking_time'
        )

    @staticmethod
    def validate_cooking_time(cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError('Время приготовления должно быть >= 1!')
        return cooking_time


class RecipeAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time'
        )


class SubscribeSerializer(serializers.ModelSerializer):
    recipes = RecipeAuthorSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = Subscription
        fields = (
            'pk', 'author',
            #'subscriber',
            'recipes', 'recipes_count'
        )
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            # 'is_subscribed',
            'recipes',
            'recipes_count'
        )
