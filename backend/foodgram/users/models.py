from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    first_name = models.CharField('Имя', max_length=150, blank=False)
    last_name = models.CharField('Фамилия', max_length=150, blank=False)
    email = models.EmailField('Email', blank=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.get_username()}'


class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriber')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        # constraints = models.UniqueConstraint(
        #     fields=['subscriber', 'author'],
        #     name='unique_author'
        # )

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
