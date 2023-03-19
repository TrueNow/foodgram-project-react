from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.models import Tag, Ingredient, Recipe, IngredientAmount


User = get_user_model()


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


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.subscriber.filter(author=obj).exists()


class MetaRecipe(serializers.SerializerMetaclass):
    model = Recipe
    fields = (
        'id', 'ingredients', 'tags',
        'is_favorited', 'is_in_shopping_cart',
        'author', 'name', 'image', 'text', 'cooking_time'
    )


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientAmountSerializer(many=True, read_only=True)
    author = AuthorSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta(MetaRecipe):
        pass

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.favorite.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.shopping_cart.filter(recipe=obj).exists()


class RecipeCreateSerializer(RecipeGetSerializer):
    tags = serializers.SlugRelatedField(
        slug_field='id', many=True, queryset=Tag.objects.all()
    )
    ingredients = serializers.SlugRelatedField(
        slug_field='id', many=True, queryset=Ingredient.objects.all()
    )
    author = serializers.SlugRelatedField(
        slug_field='id', queryset=User.objects.all()
    )

    class Meta(MetaRecipe):
        pass

    @staticmethod
    def validate_cooking_time(cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError('Время приготовления должно быть >= 1!')
        if cooking_time > 1440:
            raise serializers.ValidationError('Время приготовления должно быть больше суток!')
        return cooking_time

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(instance)
        return serializer.data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartDownloadSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('name', 'ingredients')
