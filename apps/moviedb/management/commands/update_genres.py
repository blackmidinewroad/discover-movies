from django.core.management.base import BaseCommand
from apps.moviedb.models import Genre
from apps.moviedb.tmdb.api import TMDB


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

        tmdb = TMDB()
        genres = tmdb.fetch_genres(language=language)

        for genre in genres:
            _, created = Genre.objects.update_or_create(tmdb_genre_id=genre['id'], defaults={'name': genre['name']})
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} genre: {genre["name"]}'))
