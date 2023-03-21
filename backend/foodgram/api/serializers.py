from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.models import Tag, Ingredient, Recipe, IngredientAmount
from drf_extra_fields.fields import Base64ImageField

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'amount', 'measurement_unit')


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


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartDownloadSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('ingredients',)

    def get_ingredients(self, obj):
        ingredients = IngredientAmount.objects.filter(recipe=obj)
        return IngredientAmountGetSerializer(ingredients, many=True).data


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags',
            'is_favorited', 'is_in_shopping_cart',
            'author', 'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj):
        ingredients = IngredientAmount.objects.filter(recipe=obj)
        return IngredientAmountGetSerializer(ingredients, many=True).data

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


class IngredientAmountCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')

    @staticmethod
    def validate_amount(amount):
        if amount <= 0:
            raise serializers.ValidationError('Время приготовления должно быть >= 1!')
        return amount

    def to_representation(self, instance):
        serializer = IngredientAmountGetSerializer(instance)
        return serializer.data


class RecipeCreateSerializer(RecipeGetSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientAmountCreateSerializer(many=True)
    cooking_time = serializers.IntegerField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('author',)

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(instance)
        return serializer.data

    def create(self, validated_data):
        ingredient_amounts = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        ingredients = list()

        for ingredient_amount in ingredient_amounts:
            ingredient = ingredient_amount.get('id')
            amount = ingredient_amount.get('amount')
            IngredientAmount.objects.create(recipe=recipe, ingredient=ingredient, amount=amount)
            ingredients.append(ingredient.id)

        recipe.tags.set(tags)
        recipe.ingredients.set(ingredients)
        recipe.save()
        return recipe

    def validate_name(self, name):
        if Recipe.objects.filter(author=self.context.get('request').user, name=name).exists():
            raise serializers.ValidationError('Рецепт с таким названием уже существует!')
        return name

    @staticmethod
    def validate_cooking_time(cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError('Время приготовления должно быть >= 1!')
        if cooking_time > 1440:
            raise serializers.ValidationError('Время приготовления должно быть больше суток!')
        return cooking_time

    @staticmethod
    def validate_ingredients(ingredients):
        if not ingredients:
            raise serializers.ValidationError('Рецепт не может быть без ингредиентов.')
        ingredients_set = list()
        for ingredient in ingredients:
            ingredient_obj = ingredient.get('id')
            if ingredient_obj.id in ingredients_set:
                raise serializers.ValidationError(f'Ингредиент "{ingredient_obj.name}" повторяется.')
            ingredients_set.append(ingredient_obj.id)
        return ingredients

    @staticmethod
    def validate_tags(tags):
        if len(tags) > len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться!')
        return tags
