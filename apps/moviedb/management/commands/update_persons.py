from datetime import date

from django.core.management.base import BaseCommand

from apps.moviedb.models import Person
from apps.moviedb.tmdb.api import asyncTMDB
from apps.moviedb.tmdb.id_exports import IDExport


class Command(BaseCommand):
    help = 'Update person table'

    GENDERS = {0: '', 1: 'F', 2: 'M', 3: 'NB'}

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "DD_MM_YYYY" format.',
        )

        parser.add_argument(
            '--batch_size',
            type=int,
            default=100,
            help='Number of persons to fetch per batch.',
        )

        parser.add_argument(
            '--specific_ids',
            type=int,
            default=None,
            nargs='*',
            help='Update specific persons.',
        )

        parser.add_argument(
            '--create',
            action='store_true',
            default=False,
            help='Only create new persons.',
        )

        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to "en-US".',
        )

        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of persons added.',
        )

        parser.add_argument(
            '--sort_by_popularity',
            action='store_true',
            default=False,
            help='Sort IDs by popularity if possible.',
        )

    def handle(self, *args, **kwargs):
        specific_ids = kwargs['specific_ids']
        batch_size = kwargs['batch_size']
        language = kwargs['language']
        limit = kwargs['limit']
        sort_by_popularity = ['sort_by_popularity']

        async_tmdb = asyncTMDB()

        if specific_ids is None:
            published_date = kwargs['date']
            id_export = IDExport()
            person_ids = id_export.fetch_ids('person', published_date=published_date, sort_by_popularity=sort_by_popularity)
        else:
            person_ids = specific_ids

        if kwargs['create']:
            existing_ids = set(Person.objects.all().values_list('tmdb_id', flat=True))
            person_ids = [id for id in person_ids if id not in existing_ids]

        persons = async_tmdb.batch_fetch_persons_by_id(person_ids[:limit], batch_size=batch_size, language=language)
        total = len(persons)
        count_processed = 0

        for person in persons:
            _, created = Person.objects.update_or_create(
                tmdb_id=person['id'],
                defaults={
                    'name': person['name'],
                    'imdb_id': person['imdb_id'] or '',
                    'known_for_department': person['known_for_department'] or '',
                    'biography': person['biography'] or '',
                    'place_of_birth': person['place_of_birth'] or '',
                    'gender': self.GENDERS[person['gender']],
                    'birthday': date.fromisoformat(person['birthday']) if person['birthday'] else None,
                    'deathday': date.fromisoformat(person['deathday']) if person['deathday'] else None,
                    'profile_path': person['profile_path'] or '',
                    'tmdb_popularity': person['popularity'],
                },
            )

            count_processed += created

        self.stdout.write(self.style.SUCCESS(f'Created {count_processed}/{total} persons'))
