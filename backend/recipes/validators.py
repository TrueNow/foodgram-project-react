from django.core import validators
from django.utils.deconstruct import deconstructible


MinValueValidator = validators.MinValueValidator
MaxValueValidator = validators.MaxValueValidator


@deconstructible
class TagSlugValidator(validators.RegexValidator):
    regex = r'^[a-zA-Z]{1}[-a-zA-Z0-9_]+$'
    message = 'Тег должен состоять из букв и цифр.'


@deconstructible
class HexColorValidator(validators.RegexValidator):
    regex = r'^#([A-Fa-f0-9]{6})$'
    message = 'Невозможный Hex-тег.'
