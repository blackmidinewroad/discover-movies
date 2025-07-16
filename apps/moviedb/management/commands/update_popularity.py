import logging

from django.core.management.base import BaseCommand

from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Movie, Person
from apps.services.utils import runtime

logger = logging.getLogger('moviedb')


class Command(BaseCommand):
    help = 'Update popularity of movies or people from TMDB'

    def add_arguments(self, parser):
        parser.add_argument(
            'data_type',
            type=str,
            choices=['movie', 'person'],
            help='Chose what to update: "movie" or "person".',
        )

        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "MM_DD_YYYY" format.',
        )

        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Update N most popular.',
        )

    @runtime
    def handle(self, *args, **options):
        data_type = options['data_type']
        published_date = options['date']
        limit = options['limit']

        Model = Movie if data_type == 'movie' else Person

        ids = IDExport().fetch_ids(data_type, published_date=published_date, sort_by_popularity=True, include_popularity=True)
        if ids is None:
            return
        popularity = {id: popularity for id, popularity in ids[:limit]}
        existing_objs = Model.objects.only('tmdb_id', 'tmdb_popularity')

        to_update = [obj for obj in existing_objs if obj.tmdb_id in popularity and obj.tmdb_popularity != popularity[obj.tmdb_id]]

        logger.info('Starting to update %s %ss', len(to_update), data_type)

        for obj in to_update:
            obj.tmdb_popularity = popularity[obj.tmdb_id]

        Model.objects.bulk_create(to_update, update_conflicts=True, update_fields=['tmdb_popularity'], unique_fields=['tmdb_id'])
