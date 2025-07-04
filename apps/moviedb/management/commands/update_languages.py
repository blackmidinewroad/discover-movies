from django.core.management.base import BaseCommand
from pycountry import languages

from apps.moviedb.models import Language


class Command(BaseCommand):
    help = 'Update language table'

    def handle(self, *args, **kwargs):
        for language in languages:
            if hasattr(language, 'alpha_2'):
                _, created = Language.objects.update_or_create(code=language.alpha_2, defaults={'name': language.name})
                action = 'Created' if created else 'Updated'
                self.stdout.write(self.style.SUCCESS(f'{action} language: {language.name}'))
