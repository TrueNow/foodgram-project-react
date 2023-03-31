import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Import data from ingredients.csv"

    def handle(self, *args, **options):
        with open('data/ingredients.csv', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            ingredients = [
                Ingredient(name=name, measurement_unit=unit) for name, unit in reader
            ]
            Ingredient.objects.bulk_create(ingredients)
