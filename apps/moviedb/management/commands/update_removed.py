import logging

from django.core.management.base import BaseCommand, CommandError

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Collection, Movie, Person, ProductionCompany
from apps.services.utils import runtime

logger = logging.getLogger('moviedb')


class Command(BaseCommand):
    help = 'Update entries that were removed from TMDB.'

    def add_arguments(self, parser):
        parser.add_argument(
            'data_type',
            type=str,
            choices=['movie', 'person', 'collection', 'company'],
            help='Operation to perform: movie, person, collection or company',
        )

    @runtime
    def handle(self, *args, **options):
        data_type = options['data_type']
        export_ids = IDExport().fetch_ids(data_type)
        if export_ids is None:
            return
        tmdb = asyncTMDB()

        match data_type:
            case 'movie':
                Model = Movie
                missing_export_ids = list(
                    Model.objects.filter(removed_from_tmdb=False).exclude(tmdb_id__in=export_ids).values_list('tmdb_id', flat=True)
                )
                _, not_fetched_ids = tmdb.fetch_movies_by_id(missing_export_ids, batch_size=1000)
            case 'person':
                Model = Person
                missing_export_ids = list(
                    Model.objects.filter(removed_from_tmdb=False).exclude(tmdb_id__in=export_ids).values_list('tmdb_id', flat=True)
                )
                _, not_fetched_ids = tmdb.fetch_people_by_id(missing_export_ids, batch_size=1000)
            case 'collection':
                Model = Collection
                missing_export_ids = list(
                    Model.objects.filter(removed_from_tmdb=False).exclude(tmdb_id__in=export_ids).values_list('tmdb_id', flat=True)
                )
                _, not_fetched_ids = tmdb.fetch_collections_by_id(missing_export_ids, batch_size=1000)
            case 'company':
                Model = ProductionCompany
                missing_export_ids = list(
                    Model.objects.filter(removed_from_tmdb=False).exclude(tmdb_id__in=export_ids).values_list('tmdb_id', flat=True)
                )
                _, not_fetched_ids = tmdb.fetch_companies_by_id(missing_export_ids, batch_size=1000)
            case _:
                raise CommandError("Invalid data type. Choose from 'movie', 'person', 'collection', 'company'")

        removed_ids = [id for id in not_fetched_ids if id]
        objs_to_remove = Model.objects.filter(tmdb_id__in=removed_ids)
        removed_objs = []

        for removed_obj in objs_to_remove:
            removed_obj.removed_from_tmdb = True
            removed_objs.append(removed_obj)

        logger.info('%s objects to mark removed.', len(removed_objs))

        Model.objects.bulk_update(removed_objs, fields=['removed_from_tmdb'])
