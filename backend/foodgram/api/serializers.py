from django.contrib.auth import get_user_model
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, IngredientAmount, Recipe, Tag
from . import validators

User = get_user_model()


class UsersCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    @staticmethod
    def validate_username(value):
        validators.validate_username(value)
        return value

    @staticmethod
    def validate_password(value):
        validators.validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        serializer = UserGetSerializer(instance)
        return serializer.data


class UserGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous or request.user == obj:
            return False
        return obj.following.get(user=request.user).exists()


class UsersChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(max_length=128, required=True, style={'input_type': 'password'})
    current_password = serializers.CharField(max_length=128, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('new_password', 'current_password')

    def get_object(self):
        self.instance = self.context.get('request').user
        return self.instance

    def validate_current_password(self, value):
        instance = self.get_object()
        if not instance.check_password(value):
            raise serializers.ValidationError('Неверный пароль!')
        return value

    @staticmethod
    def validate_new_password(value):
        validators.validate_password(value)
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.get('new_password')
        instance.set_password(password)
        instance.save()
        return instance


class IngredientGetSerializer(serializers.ModelSerializer):
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


class TagGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeShortGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagGetSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    author = UserGetSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'is_favorited', 'is_in_shopping_cart',
            'author', 'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj):
        ingredients = IngredientAmount.objects.filter(recipe=obj)
        return IngredientAmountGetSerializer(ingredients, many=True).data

    def _get_is_param(self, obj, param):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj in request.user.param

    def get_is_favorited(self, obj):
        return self._get_is_param(obj, 'favorite')

    def get_is_in_shopping_cart(self, obj):
        return self._get_is_param(obj, 'shopping_cart')


class RecipeCreateSerializer(RecipeGetSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientAmountCreateSerializer(many=True)
    cooking_time = serializers.IntegerField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('author',)

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

    @transaction.atomic
    def create(self, validated_data):
        ingredient_amounts = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        ingredients = list()
        obj_id = (
            IngredientAmount.objects.latest('id').id + 1
            if IngredientAmount.objects.all().exists()
            else 0
        )
        for ingredient_amount in ingredient_amounts:
            kwargs = {
                'id': obj_id,
                'recipe': recipe,
                'ingredient': ingredient_amount.get('id'),
                'amount': ingredient_amount.get('amount'),
            }
            ingredients.append(IngredientAmount(**kwargs))
            obj_id += 1

        IngredientAmount.objects.bulk_create(ingredients)
        recipe.tags.set(tags)
        recipe.save()
        return recipe

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(instance)
        return serializer.data


class ShoppingCartDownloadSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountGetSerializer(many=True, source='ingredient_list')

    class Meta:
        model = Recipe
        fields = ('ingredients',)


class SubscribeSerializer(UserGetSerializer):
    recipes = RecipeShortGetSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'recipes', 'recipes_count'
        )
