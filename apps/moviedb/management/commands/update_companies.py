import logging

from django.core.management.base import BaseCommand
from django.db.models import Count

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Country, ProductionCompany
from apps.services.utils import runtime

logger = logging.getLogger('moviedb')


class Command(BaseCommand):
    help = 'Update production company table'

    def add_arguments(self, parser):
        parser.add_argument(
            'operation',
            type=str,
            choices=['daily_export', 'movie_count'],
            help='Operation to perform: daily_export or movie_count',
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
            help='Number of companies to fetch per batch. Defaults to 100.',
        )

        parser.add_argument(
            '--specific_ids',
            type=int,
            default=None,
            nargs='*',
            help='Add only specific companies, provide TMDB IDs.',
        )

    @runtime
    def handle(self, *args, **options):
        operation = options['operation']
        match operation:
            case 'daily_export':
                self.daily_export(**options)
            case 'movie_count':
                self.update_movie_count()

    def daily_export(self, **options):
        published_date = options['date']
        batch_size = options['batch_size']
        specific_ids = options['specific_ids']

        company_ids = specific_ids or IDExport().fetch_ids('company', published_date=published_date)
        if company_ids is None:
            return

        existing_ids = set(ProductionCompany.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
        company_ids = [id for id in company_ids if id not in existing_ids]

        companies, missing_ids = asyncTMDB().fetch_companies_by_id(company_ids, batch_size=batch_size)
        countries = {c.code for c in Country.objects.all()}
        company_objs = []
        new_slugs = set()
        n_created_countries = 0

        for company_data in companies:
            origin_country_code = company_data.get('origin_country')
            if origin_country_code and origin_country_code not in countries:
                Country.objects.create(code=origin_country_code, name='unknown')
                countries.add(origin_country_code)
                n_created_countries += 1

            company = ProductionCompany(
                tmdb_id=company_data['id'],
                name=company_data['name'],
                logo_path=company_data.get('logo_path') or '',
                origin_country_id=origin_country_code or None,
            )
            company.set_slug(new_slugs)
            company_objs.append(company)
            new_slugs.add(company.slug)

        ProductionCompany.objects.bulk_create(
            company_objs,
            update_conflicts=True,
            update_fields=('name', 'slug', 'logo_path', 'origin_country'),
            unique_fields=('tmdb_id',),
        )

        logger.info('Companies processed: %s.', len(companies))
        if n_created_countries:
            logger.info('Created countries: %s.', n_created_countries)
        if missing_ids:
            logger.warning("Couldn't update/create: %s.", len(missing_ids))

    def update_movie_count(self):
        companies = ProductionCompany.objects.annotate(cur_movie_count=Count('movies'))
        to_update = []

        for company in companies:
            if company.movie_count != company.cur_movie_count:
                company.movie_count = company.cur_movie_count
                to_update.append(company)

        logger.info('Companies to update: %s.', len(to_update))

        ProductionCompany.objects.bulk_update(to_update, fields=['movie_count'])
