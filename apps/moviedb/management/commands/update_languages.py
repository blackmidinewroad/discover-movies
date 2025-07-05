from django.core.management.base import BaseCommand

from apps.moviedb.models import Language
from apps.moviedb.tmdb.api import TMDB


class Command(BaseCommand):
    help = 'Update language table'
    tmdb = TMDB()

    def handle(self, *args, **kwargs):
        languages = self.tmdb.fetch_languages()

        for language in languages:
            _, created = Language.objects.update_or_create(
                code=language['iso_639_1'],
                defaults={'name': language['english_name']},
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} language: {language['english_name']}'))
