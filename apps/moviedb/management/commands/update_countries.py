from django.core.management.base import BaseCommand

from apps.moviedb.models import Country
from apps.moviedb.tmdb.api import TMDB


class Command(BaseCommand):
    help = 'Update country table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to "en-US".',
        )

    def handle(self, *args, **kwargs):
        language = kwargs['language']

        tmdb = TMDB()
        countries = tmdb.fetch_countries(language)

        for country in countries:
            _, created = Country.objects.update_or_create(
                code=country['iso_3166_1'],
                defaults={'name': country['english_name']},
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} country: {country['english_name']}'))
