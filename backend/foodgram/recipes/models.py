from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Tags(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField(unique=True)


class Ingredients(models.Model):
    name = models.CharField(max_length=50)
    amount = models.IntegerField()
    measurement_unit = models.CharField(max_length=20)


class Recipes(models.Model):
    author = models.ForeignKey(User, related_name='recipes', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='recipes/images/', null=True, default=None)
    text = models.TextField()
    ingredients = models.ManyToManyField(Ingredients)
    tags = models.ManyToManyField(Tags)
    cooking_time = models.IntegerField()
