import logging
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Person
from apps.services.utils import runtime

logger = logging.getLogger('moviedb')


class Command(BaseCommand):
    help = 'Update person table'

    GENDERS = {0: '', 1: 'F', 2: 'M', 3: 'NB'}

    def add_arguments(self, parser):
        parser.add_argument(
            'operation',
            type=str,
            choices=['update_changed', 'daily_export', 'specific_ids', 'roles_count'],
            help='Operation to perform: update_changed, daily_export, specific_ids or roles_count',
        )

        parser.add_argument(
            '--ids',
            type=int,
            default=None,
            nargs='*',
            help='TMDB IDs of people to add (required for specific_ids operation).',
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
            default=1,
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

    @runtime
    def handle(self, *args, **options):
        operation = options['operation']
        if operation == 'roles_count':
            self.update_roles_count()
        else:
            self.full_update(**options)

    def full_update(self, **options):
        operation = options['operation']
        ids = options['ids']
        published_date = options['date']
        days = options['days']
        batch_size = options['batch_size']
        language = options['language']
        limit = options['limit']
        sort_by_popularity = options['sort_by_popularity']

        is_update = operation == 'update_changed'

        tmdb = asyncTMDB()

        match operation:
            case 'update_changed':
                person_ids, earliest_date = tmdb.fetch_changed_ids('person', days=days)

                # Get person IDs that were last updated before the changes earliest date
                person_ids = list(
                    Person.objects.filter(
                        last_update__lt=earliest_date,
                        tmdb_id__in=person_ids,
                    ).values_list('tmdb_id', flat=True)
                )
                logger.info('People to update: %s.', len(person_ids))
            case 'daily_export':
                existing_ids = set(Person.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
                person_ids = IDExport().fetch_ids('person', published_date=published_date, sort_by_popularity=sort_by_popularity)
                if person_ids is None:
                    return
            case 'specific_ids':
                if ids is None:
                    raise CommandError('Must provide --ids using specific_ids operation')
                existing_ids = set(Person.objects.filter(tmdb_id__in=ids).values_list('tmdb_id', flat=True))
                person_ids = ids
            case _:
                raise CommandError("Invalid operation. Choose from 'update_changed', 'daily_export', 'specific_ids'")

        if not is_update:
            person_ids = [id for id in person_ids if id not in existing_ids]

        if limit is not None:
            person_ids = person_ids[:limit]

        logger.info('Starting to fetch %s people...', len(person_ids))

        people, missing_ids = tmdb.fetch_people_by_id(person_ids, batch_size=batch_size, language=language)

        logger.info('Finished fetching people.')

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
            'adult',
        ]

        # Also add slug and created_at fields if not updating changes
        if not is_update:
            update_fields.extend(['slug', 'created_at'])

        logger.info('Starting to process people...')

        for person_data in people:
            birthday = deathday = None
            try:
                if person_data.get('birthday'):
                    birthday = date.fromisoformat(person_data.get('birthday'))
                if person_data.get('deathday'):
                    deathday = date.fromisoformat(person_data.get('deathday'))
            except ValueError:
                pass

            person = Person(
                tmdb_id=person_data['id'],
                name=person_data['name'],
                imdb_id=person_data.get('imdb_id') or '',
                known_for_department=person_data.get('known_for_department') or '',
                biography=person_data.get('biography') or '',
                place_of_birth=person_data.get('place_of_birth') or '',
                gender=self.GENDERS[person_data.get('gender', 0)],
                birthday=birthday,
                deathday=deathday,
                profile_path=person_data.get('profile_path') or '',
                tmdb_popularity=person_data.get('popularity', 0),
                adult=person_data.get('adult', False),
            )

            # Create new slug if not updating changes
            if not is_update:
                person.set_slug(new_slugs)
                new_slugs.add(person.slug)

            person.update_last_modified()
            person_objs.append(person)

        Person.objects.bulk_create(
            person_objs,
            update_conflicts=True,
            update_fields=update_fields,
            unique_fields=('tmdb_id',),
        )

        logger.info('People processed: %s.', len(people))
        if missing_ids:
            logger.warning("Couldn't update/create: %s (IDs: %s).", len(missing_ids), ', '.join(map(str, missing_ids)))

    def update_roles_count(self):
        people = Person.objects.annotate(
            n_cast_roles=Count('cast_roles__movie', distinct=True),
            n_crew_roles=Count('crew_roles__movie', distinct=True),
        ).only('cast_roles_count', 'crew_roles_count')
        to_update = []

        for person in people:
            cast_changed = person.cast_roles_count != person.n_cast_roles
            crew_changed = person.crew_roles_count != person.n_crew_roles
            if cast_changed:
                person.cast_roles_count = person.n_cast_roles
            if crew_changed:
                person.crew_roles_count = person.n_crew_roles
            if cast_changed or crew_changed:
                to_update.append(person)

        logger.info('People to update: %s.', len(to_update))

        Person.objects.bulk_update(to_update, fields=['cast_roles_count', 'crew_roles_count'])
