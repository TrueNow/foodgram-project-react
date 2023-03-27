from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField(verbose_name='Имя', max_length=150, blank=False)
    last_name = models.CharField(verbose_name='Фамилия', max_length=150, blank=False)
    email = models.EmailField(verbose_name='Email', blank=False, unique=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.get_username()


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        to=User, verbose_name='Подписчик', on_delete=models.CASCADE, related_name='subscriber'
    )
    author = models.ForeignKey(
        to=User, verbose_name='Автор', on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscription'
            )
        ]
        ordering = ('id',)

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
