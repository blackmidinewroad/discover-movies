from django.core.management.base import BaseCommand

from apps.moviedb.models import Country, ProductionCompany
from apps.moviedb.tmdb.api import asyncTMDB
from apps.moviedb.tmdb.id_exports import IDExport


class Command(BaseCommand):
    help = 'Update production company table'

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
            help='Number of companies to fetch per batch.',
        )

        parser.add_argument(
            '--specific_ids',
            type=int,
            default=None,
            nargs='*',
            help='Update specific companies.',
        )

        parser.add_argument(
            '--create',
            action='store_true',
            default=False,
            help='Only create new companies.',
        )

    def handle(self, *args, **kwargs):
        specific_ids = kwargs['specific_ids']
        batch_size = kwargs['batch_size']

        async_tmdb = asyncTMDB()

        if specific_ids is None:
            published_date = kwargs['date']
            id_export = IDExport()
            company_ids = id_export.fetch_ids('company', published_date=published_date)
        else:
            company_ids = specific_ids

        if kwargs['create']:
            existing_ids = set(ProductionCompany.objects.all().values_list('tmdb_id', flat=True))
            company_ids = [id for id in company_ids if id not in existing_ids]

        companies, _ = async_tmdb.batch_fetch_companies_by_id(company_ids, batch_size=batch_size)
        total = len(companies)
        count_processed = 0

        for company in companies:
            country = None
            if company['origin_country']:
                country, _ = Country.objects.get_or_create(code=company['origin_country'], defaults={'name': 'unknown'})

            _, created = ProductionCompany.objects.update_or_create(
                tmdb_id=company['id'],
                defaults={
                    'name': company['name'],
                    'logo_path': company['logo_path'] or '',
                    'origin_country': country,
                },
            )

            count_processed += created

        self.stdout.write(self.style.SUCCESS(f'Created {count_processed}/{total} companies'))
