import logging

from django.core.management.base import BaseCommand, CommandError

from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Collection, Movie, Person, ProductionCompany
from apps.services.utils import runtime

logger = logging.getLogger('moviedb')


class Command(BaseCommand):
    help = 'Clean stale data - remove entries that were deleted from TMDB.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        pass
