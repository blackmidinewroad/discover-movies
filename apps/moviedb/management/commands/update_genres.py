from django.core.management.base import BaseCommand

from apps.moviedb.integrations.tmdb.api import TMDB
from apps.moviedb.models import Genre


class Command(BaseCommand):
    help = 'Update genre table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            help='Language in ISO 639-1 code (e.g. en, fr, ru). Defaults to "en".',
        )

    def handle(self, *args, **kwargs):
        language = kwargs['language']

        genres = TMDB().fetch_genres(language=language)
        count_created = count_updated = 0

        for genre in genres:
            _, created = Genre.objects.update_or_create(
                tmdb_id=genre['id'],
                defaults={'name': genre['name']},
            )

            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(self.style.SUCCESS(f'Genres proccessed: {len(genres)} (created: {count_created}, updated: {count_updated})'))
