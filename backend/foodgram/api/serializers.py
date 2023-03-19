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


class IngredientAmountGetSerializer(serializers.ModelSerializer):
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


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartDownloadSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountGetSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('name', 'ingredients')


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientAmountGetSerializer(many=True, read_only=True)
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


class IngridientAmoutCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError('Время приготовления должно быть >= 1!')
        return amount


class RecipeCreateSerializer(RecipeGetSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngridientAmoutCreateSerializer(many=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags',
            'name',
            # 'image',
            'text', 'cooking_time'
        )
        read_only_fields = ('author',)

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(instance)
        return serializer.data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        obj_id = (
            IngredientAmount.objects.latest('id').id + 1
            if IngredientAmount.objects.all().exists()
            else 0
        )
        temp_ingredients = list()
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id').id
            amount = ingredient.get('amount')

            ingredient_obj = IngredientAmount.objects.filter(
                ingredient_id=ingredient_id,
                amount=amount
            )

            if not ingredient_obj.exists():
                temp_ingredients.append(
                    IngredientAmount(
                        id=obj_id,
                        recipe=recipe,
                        ingredient_id=ingredient_id,
                        amount=amount
                    )
                )
                obj_id += 1

        IngredientAmount.objects.bulk_create(
            temp_ingredients, batch_size=999
        )
        # recipe.image = image
        recipe.save()
        return recipe

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

    def validate_tags(self, tags):
        if len(tags) > len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться!')
        return tags
