from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField('Имя', max_length=150, blank=False)
    last_name = models.CharField('Фамилия', max_length=150, blank=False)
    email = models.EmailField('Email', blank=False)


class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriber')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = models.UniqueConstraint(
            fields=['user', 'author'],
            name='unique_following'
        )

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
