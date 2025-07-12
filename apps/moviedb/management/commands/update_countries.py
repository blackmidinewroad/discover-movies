from django.core.management.base import BaseCommand

from apps.moviedb.integrations.tmdb.api import TMDB
from apps.moviedb.models import Country


class Command(BaseCommand):
    help = 'Update country table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-US, fr-CA, de-DE). Defaults to "en-US".',
        )

    def handle(self, *args, **options):
        language = options['language']

        countries = TMDB().fetch_countries(language)
        country_objs = []
        new_slugs = set()

        for country_data in countries:
            country = Country(code=country_data['iso_3166_1'], name=country_data['english_name'])
            country.set_slug(new_slugs)
            country_objs.append(country)
            new_slugs.add(country.slug)

        Country.objects.bulk_create(
            country_objs,
            update_conflicts=True,
            update_fields=('name', 'slug'),
            unique_fields=('code',),
        )

        self.stdout.write(self.style.SUCCESS(f'Countries processed: {len(countries)}'))
