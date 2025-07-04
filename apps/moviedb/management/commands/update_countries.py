from django.core.management.base import BaseCommand
from pycountry import countries

from apps.moviedb.models import Country


class Command(BaseCommand):
    help = 'Update country table'

    def handle(self, *args, **kwargs):
        for country in countries:
            _, created = Country.objects.update_or_create(code=country.alpha_2, defaults={'name': country.name})
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} country: {country.name}'))
