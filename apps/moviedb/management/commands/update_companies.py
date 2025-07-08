from django.core.management.base import BaseCommand

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Country, ProductionCompany


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

        if specific_ids is None:
            published_date = kwargs['date']
            id_export = IDExport()
            company_ids = id_export.fetch_ids('company', published_date=published_date)
        else:
            company_ids = specific_ids

        if kwargs['create']:
            existing_ids = set(ProductionCompany.objects.all().values_list('tmdb_id', flat=True))
            company_ids = [id for id in company_ids if id not in existing_ids]

        companies, missing_ids = asyncTMDB().batch_fetch_companies_by_id(company_ids, batch_size=batch_size)
        count_created = count_updated = 0

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

            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'Companies proccessed: {len(companies)} (created: {count_created}, updated: {count_updated})')
        )
        if missing_ids:
            self.stdout.write(self.style.WARNING(f"Couldn't update/create: {len(missing_ids)} (IDs: {', '.join(map(str, missing_ids))})"))
