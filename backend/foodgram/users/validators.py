from rest_framework import exceptions

from .models import BANNED_USERNAMES


def validate_username(value):
    value = value.lower()
    if value in BANNED_USERNAMES:
        raise exceptions.ValidationError('Некорректное имя пользователя.')
    return value
