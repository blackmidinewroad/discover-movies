from django.core.management.base import BaseCommand

from apps.moviedb.integrations.tmdb.api import TMDB
from apps.moviedb.models import Language


class Command(BaseCommand):
    help = 'Update language table'

    def handle(self, *args, **options):
        languages = TMDB().fetch_languages()
        language_objs = []
        new_slugs = set()

        for language_data in languages:
            language = Language(code=language_data['iso_639_1'], name=language_data['english_name'])
            language.set_slug(new_slugs)
            language_objs.append(language)
            new_slugs.add(language.slug)

        Language.objects.bulk_create(
            language_objs,
            update_conflicts=True,
            update_fields=('name', 'slug'),
            unique_fields=('code',),
        )

        self.stdout.write(self.style.SUCCESS(f'Languages processed: {len(languages)}'))
