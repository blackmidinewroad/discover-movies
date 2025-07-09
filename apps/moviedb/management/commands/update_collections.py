from django.core.management.base import BaseCommand

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Collection


class Command(BaseCommand):
    help = 'Update collection table'

    def add_arguments(self, parser):
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
            help='Number of collections to fetch per batch. Defaults to 100.',
        )

        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to "en-US".',
        )

        parser.add_argument(
            '--specific_ids',
            type=int,
            default=None,
            nargs='*',
            help='Update specific collections.',
        )

        parser.add_argument(
            '--create',
            action='store_true',
            default=False,
            help='Only create new collections.',
        )

    def handle(self, *args, **options):
        published_date = options['date']
        batch_size = options['batch_size']
        language = options['language']
        specific_ids = options['specific_ids']
        only_create = options['create']

        collection_ids = specific_ids or IDExport().fetch_ids('collection', published_date=published_date)

        if only_create:
            existing_ids = set(Collection.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
            collection_ids = [id for id in collection_ids if id not in existing_ids]

        collections, missing_ids = asyncTMDB().batch_fetch_collections_by_id(collection_ids, batch_size=batch_size, language=language)
        collection_objs = []
        new_slugs = set()

        for collection_data in collections:
            collection = Collection(
                tmdb_id=collection_data['id'],
                name=collection_data['name'],
                overview=collection_data['overview'] or '',
                poster_path=collection_data['poster_path'] or '',
                backdrop_path=collection_data['backdrop_path'] or '',
            )
            collection.set_slug(collection.name, new_slugs)
            collection_objs.append(collection)
            new_slugs.add(collection.slug)

        Collection.objects.bulk_create(
            collection_objs,
            update_conflicts=True,
            update_fields=('name', 'slug', 'overview', 'poster_path', 'backdrop_path'),
            unique_fields=('tmdb_id',),
        )

        self.stdout.write(self.style.SUCCESS(f'Collections processed: {len(collections)}'))
        if missing_ids:
            self.stdout.write(self.style.WARNING(f"Couldn't update/create: {len(missing_ids)} (IDs: {', '.join(map(str, missing_ids))})"))
