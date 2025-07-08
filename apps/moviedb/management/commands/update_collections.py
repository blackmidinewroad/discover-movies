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
            help='Date of the export file in "DD_MM_YYYY" format.',
        )

        parser.add_argument(
            '--batch_size',
            type=int,
            default=100,
            help='Number of collections to fetch per batch.',
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

        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to "en-US".',
        )

    def handle(self, *args, **kwargs):
        specific_ids = kwargs['specific_ids']
        batch_size = kwargs['batch_size']
        language = kwargs['language']

        if specific_ids is None:
            published_date = kwargs['date']
            id_export = IDExport()
            collection_ids = id_export.fetch_ids('collection', published_date=published_date)
        else:
            collection_ids = specific_ids

        if kwargs['create']:
            existing_ids = set(Collection.objects.all().values_list('tmdb_id', flat=True))
            collection_ids = [id for id in collection_ids if id not in existing_ids]

        collections, missing_ids = asyncTMDB().batch_fetch_collections_by_id(collection_ids, batch_size=batch_size, language=language)
        count_created = count_updated = 0

        for collection in collections:
            _, created = Collection.objects.update_or_create(
                tmdb_id=collection['id'],
                defaults={
                    'name': collection['name'],
                    'overview': collection['overview'] or '',
                    'poster_path': collection['poster_path'] or '',
                    'backdrop_path': collection['backdrop_path'] or '',
                },
            )

            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'Collections proccessed: {len(collections)} (created: {count_created}, updated: {count_updated})')
        )
        if missing_ids:
            self.stdout.write(self.style.WARNING(f"Couldn't update/create: {len(missing_ids)} (IDs: {', '.join(map(str, missing_ids))})"))
