from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.models import Subscription
from recipes.models import Ingredient, IngredientAmount, Recipe, Tag, Favorite, ShoppingCart
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
    ingredients = serializers.SerializerMethodField(read_only=True)
    author = UserGetSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'is_favorited', 'is_in_shopping_cart',
            'author', 'name', 'image', 'text', 'cooking_time'
        )

    @staticmethod
    def get_ingredients(obj):
        ingredients = IngredientAmount.objects.filter(recipe=obj)
        return IngredientAmountGetSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        return obj.id in self.context.get('favorite_recipes', [])

    def get_is_in_shopping_cart(self, obj):
        return obj.id in self.context.get('shopping_recipes', [])


class RecipeCreateSerializer(serializers.ModelSerializer):
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

    @staticmethod
    def _ingredients(instance, ingredients):
        create_ingredients = list()
        obj_id = (
            IngredientAmount.objects.latest('id').id + 1
            if IngredientAmount.objects.all().exists()
            else 0
        )
        for ingredient in ingredients:
            kwargs = {
                'id': obj_id,
                'recipe': instance,
                'ingredient': ingredient.get('id'),
                'amount': ingredient.get('amount'),
            }
            create_ingredients.append(IngredientAmount(**kwargs))
            obj_id += 1

        IngredientAmount.objects.bulk_create(create_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().create(validated_data)
        instance.tags.set(tags)
        self._ingredients(instance, ingredients)

        instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.get('tags')
        if tags:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)

        ingredients = validated_data.get('ingredients')
        if ingredients:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self._ingredients(instance, ingredients)
            instance.save()

        instance = super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(instance)
        return serializer.data


class ShoppingCartDownloadSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountGetSerializer(many=True, source='ingredient_list')

    class Meta:
        model = Recipe
        fields = ('ingredients',)


class SubscriberGetSerializer(serializers.ModelSerializer):
    recipes = RecipeShortGetSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'recipes', 'recipes_count'
        )


class FavoriteOrShoppingCreateSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        try:
            instance = self.Meta.model.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'errors': 'Рецепт уже добавлен!'})
        return instance

    def delete(self, validated_data):
        try:
            self.Meta.model.objects.get(**validated_data).delete()
        except self.Meta.model.DoesNotExist:
            raise serializers.ValidationError({'errors': 'Рецепта не найдено.'})
        return

    def to_representation(self, instance):
        return RecipeShortGetSerializer(instance=instance.recipe).data


class FavoriteCreateSerializer(FavoriteOrShoppingCreateSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCreateSerializer(FavoriteOrShoppingCreateSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class SubscriptionCreateSerializer(FavoriteOrShoppingCreateSerializer):
    class Meta:
        model = Subscription
        fields = ('subscriber', 'author')

    def to_representation(self, instance):
        return SubscriberGetSerializer(instance=instance.author).data
