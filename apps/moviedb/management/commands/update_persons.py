from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Person


class Command(BaseCommand):
    help = 'Update person table'

    GENDERS = {0: '', 1: 'F', 2: 'M', 3: 'NB'}

    def add_arguments(self, parser):
        parser.add_argument(
            'operation',
            type=str,
            choices=['update_changed', 'daily_export', 'specific_ids'],
            help='Operation to perform: update_changed, daily_export or specific_ids',
        )

        parser.add_argument(
            '--ids',
            type=int,
            default=None,
            nargs='*',
            help='IDs to ceate/update (required for specific_ids operation).',
        )

        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "MM_DD_YYYY" format.',
        )

        parser.add_argument(
            '--batch_size',
            type=int,
            default=100,
            help='Number of persons to fetch per batch.',
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

        parser.add_argument(
            '--create',
            action='store_true',
            default=False,
            help="Only create new persons (can't be used with update_changed operation).",
        )

    def handle(self, *args, **options):
        operation = options['operation']
        published_date = options['date']
        ids = options['ids']
        batch_size = options['batch_size']
        language = options['language']
        limit = options['limit']
        sort_by_popularity = options['sort_by_popularity']
        only_create = options['create']

        # IDs of persons already in db
        existing_ids = set(Person.objects.only('tmdb_id').values_list('tmdb_id', flat=True))

        match operation:
            case 'update_changed':
                if only_create:
                    raise CommandError("Can't use --create with update_changed operation")
                person_ids = []
                person_ids = [id for id in person_ids if id in existing_ids]
            case 'daily_export':
                person_ids = IDExport().fetch_ids('person', published_date=published_date, sort_by_popularity=sort_by_popularity)
            case 'specific_ids':
                if ids is None:
                    raise CommandError('Must provide --ids using specific_ids operation')
                person_ids = ids
            case _:
                raise CommandError("Invalid operation. Choose from 'update_changed', 'daily_export', 'specific_ids'")

        if only_create:
            person_ids = [id for id in person_ids if id not in existing_ids]

        persons, missing_ids = asyncTMDB().batch_fetch_persons_by_id(person_ids[:limit], batch_size=batch_size, language=language)
        person_objs = []
        new_slugs = set()

        for person_data in persons:
            person = Person(
                tmdb_id=person_data['id'],
                name=person_data['name'],
                imdb_id=person_data['imdb_id'] or '',
                known_for_department=person_data['known_for_department'] or '',
                biography=person_data['biography'] or '',
                place_of_birth=person_data['place_of_birth'] or '',
                gender=self.GENDERS[person_data['gender']],
                birthday=date.fromisoformat(person_data['birthday']) if person_data['birthday'] else None,
                deathday=date.fromisoformat(person_data['deathday']) if person_data['deathday'] else None,
                profile_path=person_data['profile_path'] or '',
                tmdb_popularity=person_data['popularity'],
            )
            person.set_slug(person.name, new_slugs)
            person_objs.append(person)
            new_slugs.add(person.slug)

        Person.objects.bulk_create(
            person_objs,
            update_conflicts=True,
            update_fields=(
                'name',
                'slug',
                'imdb_id',
                'known_for_department',
                'biography',
                'place_of_birth',
                'gender',
                'birthday',
                'deathday',
                'profile_path',
                'tmdb_popularity',
            ),
            unique_fields=('tmdb_id',),
        )

        self.stdout.write(self.style.SUCCESS(f'Persons processed: {len(persons)}'))
        if missing_ids:
            self.stdout.write(self.style.WARNING(f"Couldn't update/create: {len(missing_ids)} (IDs: {', '.join(map(str, missing_ids))})"))
