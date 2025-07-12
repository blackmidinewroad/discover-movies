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

    def handle(self, *args, **options):
        language = options['language']

        genres = TMDB().fetch_genres(language=language)
        genre_objs = []
        new_slugs = set()

        for genre_data in genres:
            genre = Genre(tmdb_id=genre_data['id'], name=genre_data['name'])
            genre.set_slug(new_slugs)
            genre_objs.append(genre)
            new_slugs.add(genre.slug)

        Genre.objects.bulk_create(
            genre_objs,
            update_conflicts=True,
            update_fields=('name', 'slug'),
            unique_fields=('tmdb_id',),
        )

        self.stdout.write(self.style.SUCCESS(f'Genres processed: {len(genres)}'))
