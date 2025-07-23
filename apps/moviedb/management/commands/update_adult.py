import logging

from django.core.management.base import BaseCommand

from apps.moviedb.models import Collection, Movie
from apps.services.utils import runtime


logger = logging.getLogger('moviedb')


class Command(BaseCommand):
    help = 'Mark movies as "adult" if they belong to an adult collection'

    @runtime
    def handle(self, *args, **options):
        collections = Collection.objects.filter(adult=True).prefetch_related('movies')
        logger.info('%s adult collections.', len(collections))

        to_update = []

        for collection in collections:
            for movie in collection.movies.all():
                if not movie.adult:
                    movie.adult = True
                    to_update.append(movie)

        logger.info('%s movies to update.', len(to_update))

        Movie.objects.bulk_update(to_update, fields=['adult'])
