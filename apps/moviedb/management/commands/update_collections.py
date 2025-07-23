import logging

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, Q

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Collection
from apps.services.utils import runtime

logger = logging.getLogger('moviedb')


class Command(BaseCommand):
    help = 'Update collection table'

    def add_arguments(self, parser):
        parser.add_argument(
            'operation',
            type=str,
            choices=['daily_export', 'movies_released', 'avg_popularity'],
            help='Operation to perform: daily_export, movie_count or avg_popularity',
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
            help='Number of collections to fetch per batch. Defaults to 100.',
        )

        parser.add_argument(
            '--language',
            type=str,
            default='en-US',
            help='Locale (ISO 639-1-ISO 3166-1) code (e.g. en-US, fr-CA, de-DE). Defaults to "en-US".',
        )

        parser.add_argument(
            '--specific_ids',
            type=int,
            default=None,
            nargs='*',
            help='Add only specific collections, provide TMDB IDs.',
        )

    @runtime
    def handle(self, *args, **options):
        operation = options['operation']
        match operation:
            case 'daily_export':
                self.daily_export(**options)
            case 'movies_released':
                self.update_movies_released()
            case 'avg_popularity':
                self.update_avg_popularity()

    def daily_export(self, **options):
        published_date = options['date']
        batch_size = options['batch_size']
        language = options['language']
        specific_ids = options['specific_ids']

        collection_ids = specific_ids or IDExport().fetch_ids('collection', published_date=published_date)
        if collection_ids is None:
            return

        existing_ids = set(Collection.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
        collection_ids = [id for id in collection_ids if id not in existing_ids]

        collections, missing_ids = asyncTMDB().fetch_collections_by_id(collection_ids, batch_size=batch_size, language=language)
        collection_objs = []
        new_slugs = set()

        for collection_data in collections:
            collection = Collection(
                tmdb_id=collection_data['id'],
                name=collection_data['name'],
                overview=collection_data.get('overview') or '',
                poster_path=collection_data.get('poster_path') or '',
                backdrop_path=collection_data.get('backdrop_path') or '',
            )
            collection.set_slug(new_slugs)
            collection_objs.append(collection)
            new_slugs.add(collection.slug)

        Collection.objects.bulk_create(
            collection_objs,
            update_conflicts=True,
            update_fields=('name', 'slug', 'overview', 'poster_path', 'backdrop_path'),
            unique_fields=('tmdb_id',),
        )

        logger.info('Collections processed: %s.', len(collections))
        if missing_ids:
            logger.warning("Couldn't update/create: %s (IDs: %s).", len(missing_ids), ', '.join(map(str, missing_ids)))

    def update_movies_released(self):
        collections = Collection.objects.annotate(n_released=Count('movies__status', filter=Q(movies__status=6)))
        to_update = []

        for collection in collections:
            if collection.movies_released != collection.n_released:
                collection.movies_released = collection.n_released
                to_update.append(collection)

        logger.info('Collections to update: %s.', len(to_update))

        Collection.objects.bulk_update(to_update, fields=['movies_released'])

    def update_avg_popularity(self):
        collections = Collection.objects.annotate(cur_avg_popularity=Avg('movies__tmdb_popularity'))
        to_update = []

        for collection in collections:
            if collection.cur_avg_popularity is not None and collection.avg_popularity != collection.cur_avg_popularity:
                collection.avg_popularity = collection.cur_avg_popularity
                to_update.append(collection)

        logger.info('Collections to update: %s.', len(to_update))

        Collection.objects.bulk_update(to_update, fields=['avg_popularity'])
