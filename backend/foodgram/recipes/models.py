from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'Тег {self.name}'


class Ingredient(models.Model):
    name = models.CharField(max_length=50)
    measurement_unit = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        # constraints = models.UniqueConstraint(
        #     fields=['name', 'measurement_unit'],
        #     name='unique_name_unit'
        # )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(Ingredient, related_name='amount', on_delete=models.CASCADE)
    amount = models.IntegerField()

    class Meta:
        verbose_name = 'Ингредиент и количество'
        verbose_name_plural = 'Ингредиенты и количество'
        # constraints = models.UniqueConstraint(
        #     fields=['name', 'amount', 'measurement_unit'],
        #     name='unique_name_unit'
        # )

    def __str__(self):
        return f'{self.ingredient.name} {self.amount} {self.ingredient.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(User, related_name='recipes', on_delete=models.CASCADE, blank=False)
    name = models.CharField(max_length=50, blank=False)
    image = models.ImageField(upload_to='recipes/images/', blank=True, null=True, default=None)
    text = models.TextField(blank=False)
    ingredients = models.ManyToManyField(IngredientAmount, blank=False)
    tags = models.ManyToManyField(Tag, blank=False)
    cooking_time = models.IntegerField(blank=False)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        # constraints = models.UniqueConstraint(
        #     fields=['author', 'name'],
        #     name='unique_author_name'
        # )

    def __str__(self):
        return f'Рецепт "{self.name}" от {self.author}'


class Favorite(models.Model):
    user = models.ForeignKey(User, related_name='favorite', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='favorite', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        # constraints = models.UniqueConstraint(
        #     fields=['user', 'recipe'],
        #     name='unique_user_recipe'
        # )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное.'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, related_name='shopping_cart', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='shopping_cart', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        # constraints = models.UniqueConstraint(
        #     fields=['user', 'recipe'],
        #     name='unique_user_recipe'
        # )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в cписок покупок.'
