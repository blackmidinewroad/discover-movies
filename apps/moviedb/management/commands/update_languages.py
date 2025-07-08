from django.core.management.base import BaseCommand

from apps.moviedb.integrations.tmdb.api import TMDB
from apps.moviedb.models import Language


class Command(BaseCommand):
    help = 'Update language table'

    def handle(self, *args, **kwargs):
        languages = TMDB().fetch_languages()
        count_created = count_updated = 0

        for language in languages:
            _, created = Language.objects.update_or_create(
                code=language['iso_639_1'],
                defaults={'name': language['english_name']},
            )

            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'Languages proccessed: {len(languages)} (created: {count_created}, updated: {count_updated})')
        )
