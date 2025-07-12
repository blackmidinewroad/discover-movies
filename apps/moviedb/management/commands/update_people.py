from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Person
from apps.services.utils import runtime


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
            help='IDs to create/update (required for specific_ids operation).',
        )

        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "MM_DD_YYYY" format.',
        )

        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help=(
                'Changes made in the past N days (only works with update_changed operation).'
                'By default changes will be fetched for the past 24 hours.'
            ),
        )

        parser.add_argument(
            '--batch_size',
            type=int,
            default=100,
            help='Number of people to fetch per batch. Defaults to 100.',
        )

        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-US, fr-CA, de-DE). Defaults to "en-US".',
        )

        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of people added.',
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
            help="Only create new people (can't be used with update_changed operation).",
        )

    @runtime
    def handle(self, *args, **options):
        operation = options['operation']
        ids = options['ids']
        published_date = options['date']
        days = options['days']
        batch_size = options['batch_size']
        language = options['language']
        limit = options['limit']
        sort_by_popularity = options['sort_by_popularity']
        only_create = options['create']

        is_update = False

        tmdb = asyncTMDB()

        match operation:
            case 'update_changed':
                if only_create:
                    raise CommandError("Can't use --create with update_changed operation")

                is_update = True

                person_ids, earliest_date = tmdb.fetch_changed_ids('person', days=days)

                # Get person IDs that were last updated before the changes earliest date
                person_ids = list(
                    Person.objects.filter(
                        last_update__lt=earliest_date,
                        tmdb_id__in=person_ids,
                    ).values_list('tmdb_id', flat=True)
                )
                self.stdout.write(self.style.SUCCESS(f'People to update: {len(person_ids)}'))
            case 'daily_export':
                existing_ids = set(Person.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
                person_ids = IDExport().fetch_ids('person', published_date=published_date, sort_by_popularity=sort_by_popularity)
            case 'specific_ids':
                if ids is None:
                    raise CommandError('Must provide --ids using specific_ids operation')
                existing_ids = set(Person.objects.filter(tmdb_id__in=ids).values_list('tmdb_id', flat=True))
                person_ids = ids
            case _:
                raise CommandError("Invalid operation. Choose from 'update_changed', 'daily_export', 'specific_ids'")

        if only_create:
            person_ids = [id for id in person_ids if id not in existing_ids]

        if limit is not None:
            person_ids = person_ids[:limit]

        people, missing_ids = tmdb.fetch_people_by_id(person_ids, batch_size=batch_size, language=language)
        person_objs = []
        new_slugs = set()

        # Fields to update in person table
        update_fields = [
            'name',
            'imdb_id',
            'known_for_department',
            'biography',
            'place_of_birth',
            'gender',
            'birthday',
            'deathday',
            'profile_path',
            'tmdb_popularity',
            'last_update',
        ]

        # Also update slug if not updating changes
        if not is_update:
            update_fields.append('slug')

        for person_data in people:
            birthday = deathday = None
            try:
                if person_data['birthday']:
                    birthday = date.fromisoformat(person_data['birthday'])
                if person_data['deathday']:
                    deathday = date.fromisoformat(person_data['deathday'])
            except ValueError:
                pass

            person = Person(
                tmdb_id=person_data['id'],
                name=person_data['name'],
                imdb_id=person_data['imdb_id'] or '',
                known_for_department=person_data['known_for_department'] or '',
                biography=person_data['biography'] or '',
                place_of_birth=person_data['place_of_birth'] or '',
                gender=self.GENDERS[person_data['gender']],
                birthday=birthday,
                deathday=deathday,
                profile_path=person_data['profile_path'] or '',
                tmdb_popularity=person_data['popularity'],
            )

            # Create new slug if not updating changes
            if not is_update:
                person.set_slug(new_slugs)
                new_slugs.add(person.slug)

            person.pre_bulk_create()
            person_objs.append(person)

        Person.objects.bulk_create(
            person_objs,
            update_conflicts=True,
            update_fields=update_fields,
            unique_fields=('tmdb_id',),
        )

        self.stdout.write(self.style.SUCCESS(f'People processed: {len(people)}'))
        if missing_ids:
            self.stdout.write(self.style.WARNING(f"Couldn't update/create: {len(missing_ids)} (IDs: {', '.join(map(str, missing_ids))})"))
