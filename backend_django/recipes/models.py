from django.contrib.auth import get_user_model
from django.db import models

from . import validators


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50, unique=True)
    color = models.CharField(
        verbose_name='Цвет', max_length=7, unique=True, validators=[validators.HexColorValidator()]
    )
    slug = models.SlugField(verbose_name='Ссылка', unique=True, validators=[validators.TagSlugValidator()])

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return f'Тег {self.name}'


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Название', max_length=200, blank=False)
    measurement_unit = models.CharField(verbose_name='Размерность', max_length=20, blank=False)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        to=User, verbose_name='Автор', related_name='recipes', on_delete=models.CASCADE, blank=False
    )
    name = models.CharField(verbose_name='Название', max_length=50, blank=False)
    image = models.ImageField(
        upload_to='recipes/images/', verbose_name='Картинка', blank=False
    )
    text = models.TextField(verbose_name='Описание', blank=False)
    ingredients = models.ManyToManyField(
        to=Ingredient, verbose_name='Список ингредиентов', blank=False, through='IngredientAmount'
    )
    tags = models.ManyToManyField(
        to=Tag, verbose_name='Список тегов', blank=False
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)', blank=False, validators=[
            validators.MinValueValidator(1, message='Время приготовления должно быть >= 1!'),
            validators.MaxValueValidator(1440, message='Время приготовления должно быть больше суток!')
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации', auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_author_name'
            )
        ]

    def __str__(self):
        return f'Рецепт "{self.name}" от {self.author}'


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        to=Recipe, verbose_name='Рецепт', related_name='ingredient_list', on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        to=Ingredient, verbose_name='Ингридиент', on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество', validators=[validators.MinValueValidator(1, message='Минимальное количество = 1.')]
    )

    class Meta:
        verbose_name = 'Ингредиент (кол-во)'
        verbose_name_plural = 'Ингредиенты (кол-во)'
        ordering = ('ingredient__name',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient.name} {self.amount} {self.ingredient.measurement_unit}'


class Favorite(models.Model):
    user = models.ForeignKey(
        to=User, verbose_name='Пользователь', related_name='favorite', on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        to=Recipe, verbose_name='Рецепт', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('user', 'recipe')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное.'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        to=User, verbose_name='Пользователь', related_name='shopping_cart', on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        to=Recipe, verbose_name='Рецепт', related_name='shopping_cart', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('user', 'recipe')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в cписок покупок.'
