from django.db import models


class Tags(models.Model):
    name = models.CharField(max_length=150, unique=True)
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField(unique=True)
